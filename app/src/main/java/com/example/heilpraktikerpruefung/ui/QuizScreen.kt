package com.example.heilpraktikerpruefung.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.ArrowForward
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.example.heilpraktikerpruefung.data.ExamRepository
import com.example.heilpraktikerpruefung.data.Question
import kotlinx.coroutines.launch

private data class AnsweredQuestion(
    val selectedIndices: Set<Int>,
    val isCorrect: Boolean
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun QuizScreen(examId: String, onFinished: (Int, Int) -> Unit) {
    val context = LocalContext.current
    val repository = remember { ExamRepository(context) }

    var questions by remember { mutableStateOf<List<Question>>(emptyList()) }
    var quizTitle by remember { mutableStateOf("Laden...") }
    var isLoading by remember { mutableStateOf(true) }

    // In-memory answer tracking
    var answeredQuestions by remember { mutableStateOf<Map<Int, AnsweredQuestion>>(emptyMap()) }

    // State
    var currentQuestionIndex by remember { mutableIntStateOf(0) }
    var selectedOptionIndices by remember { mutableStateOf<Set<Int>>(emptySet()) }
    var resultMessage by remember { mutableStateOf<String?>(null) }
    var score by remember { mutableIntStateOf(0) }
    var isAnswerChecked by remember { mutableStateOf(false) }
    val scrollState = rememberScrollState()
    val isReviewMode = examId.startsWith("REVIEW")

    val scope = rememberCoroutineScope()

    LaunchedEffect(examId) {
        if (examId == "REVIEW_ALL") {
            val wrongPairs = repository.getWrongQuestions()
            questions = wrongPairs.mapNotNull { (eId, qIdx) ->
                repository.getQuestion(eId, qIdx)
            }
            quizTitle = "Wiederholung: Alle Falschen"
        } else if (examId.startsWith("REVIEW_")) {
            val actualExamId = examId.removePrefix("REVIEW_")
            val results = repository.getQuestionResults(actualExamId)
            questions = results.filter { !it.isCorrect }.mapNotNull {
                repository.getQuestion(actualExamId, it.questionIndex)
            }
            quizTitle = "Wiederholung: $actualExamId"
        } else {
            val exam = repository.getExamById(examId)
            if (exam != null) {
                questions = exam.questions
                quizTitle = "${exam.month} ${exam.year}"

                // Resume logic: check for existing progress
                val existingResults = repository.getQuestionResults(examId)
                if (existingResults.isNotEmpty()) {
                    val totalQuestions = exam.questions.size
                    if (existingResults.size >= totalQuestions) {
                        // All questions answered - clear old results, start fresh
                        repository.deleteQuestionResults(examId)
                    } else {
                        // Partial progress - restore state
                        val restored = mutableMapOf<Int, AnsweredQuestion>()
                        var restoredScore = 0
                        for (qr in existingResults) {
                            val selIndices = if (qr.selectedIndices.isNotEmpty()) {
                                qr.selectedIndices.split(",").mapNotNull { it.trim().toIntOrNull() }.toSet()
                            } else {
                                emptySet()
                            }
                            restored[qr.questionIndex] = AnsweredQuestion(
                                selectedIndices = selIndices,
                                isCorrect = qr.isCorrect
                            )
                            if (qr.isCorrect) restoredScore++
                        }
                        answeredQuestions = restored
                        score = restoredScore
                        // Jump to first unanswered question
                        val firstUnanswered = (0 until totalQuestions).firstOrNull { it !in restored }
                        currentQuestionIndex = firstUnanswered ?: 0
                    }
                }
            }
        }
        isLoading = false
    }

    if (isLoading) {
        Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            CircularProgressIndicator()
        }
        return
    }

    if (questions.isEmpty()) {
        Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            Text("Keine Fragen vorhanden!")
        }
        return
    }

    val currentQuestion = questions.getOrNull(currentQuestionIndex)
    val isViewingAnswered = currentQuestionIndex in answeredQuestions

    // When navigating to an answered question, show its saved state
    LaunchedEffect(currentQuestionIndex) {
        scrollState.scrollTo(0)
        val answered = answeredQuestions[currentQuestionIndex]
        if (answered != null) {
            selectedOptionIndices = answered.selectedIndices
            isAnswerChecked = true
            val isCorrect = answered.isCorrect
            resultMessage = if (isCorrect) "Richtig! Gut gemacht." else "Leider nicht ganz richtig."
        } else {
            selectedOptionIndices = emptySet()
            isAnswerChecked = false
            resultMessage = null
        }
    }

    // Navigation helpers
    val canGoBack = currentQuestionIndex > 0
    val canGoForward = currentQuestionIndex < questions.size - 1 && (currentQuestionIndex in answeredQuestions)

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("$quizTitle") },
                actions = {
                    // Navigation controls
                    IconButton(onClick = { currentQuestionIndex-- }, enabled = canGoBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Vorherige Frage")
                    }
                    Text(
                        "Frage ${currentQuestionIndex + 1}/${questions.size}",
                        style = MaterialTheme.typography.labelLarge,
                        modifier = Modifier.align(Alignment.CenterVertically)
                    )
                    IconButton(onClick = { currentQuestionIndex++ }, enabled = canGoForward) {
                        Icon(Icons.Default.ArrowForward, contentDescription = "Nächste Frage")
                    }
                }
            )
        }
    ) { paddingValues ->
        if (currentQuestion != null) {
            Column(
                modifier = Modifier
                    .padding(paddingValues)
                    .padding(16.dp)
                    .verticalScroll(scrollState)
            ) {
                Text(text = currentQuestion.text, style = MaterialTheme.typography.bodyLarge)
                Spacer(modifier = Modifier.height(16.dp))

                if (currentQuestion.statements.isNotEmpty()) {
                    Text(text = "Aussagen:", style = MaterialTheme.typography.titleMedium)
                    currentQuestion.statements.forEachIndexed { index, statement ->
                        Text(
                            text = "${index + 1}. $statement",
                            style = MaterialTheme.typography.bodyMedium,
                            modifier = Modifier.padding(vertical = 4.dp, horizontal = 8.dp)
                        )
                    }
                    Spacer(modifier = Modifier.height(16.dp))
                }

                currentQuestion.options.forEachIndexed { index, option ->
                    val isCorrect = currentQuestion.correctIndices.contains(index)
                    val isSelected = selectedOptionIndices.contains(index)

                    val backgroundColor = if (isAnswerChecked) {
                        if (isCorrect) Color.Green.copy(alpha = 0.2f)
                        else if (isSelected) Color.Red.copy(alpha = 0.2f)
                        else Color.Transparent
                    } else {
                        if (isSelected) MaterialTheme.colorScheme.primaryContainer else Color.Transparent
                    }

                    Surface(
                        onClick = {
                            if (!isAnswerChecked) {
                                if (currentQuestion.type == "Mehrfachauswahl") {
                                    selectedOptionIndices = if (isSelected) {
                                        selectedOptionIndices - index
                                    } else {
                                        selectedOptionIndices + index
                                    }
                                } else {
                                    selectedOptionIndices = setOf(index)
                                }
                            }
                        },
                        color = Color.Transparent,
                        modifier = Modifier.fillMaxWidth().background(backgroundColor)
                    ) {
                        Row(
                            modifier = Modifier.padding(12.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            if (currentQuestion.type == "Mehrfachauswahl") {
                                Checkbox(
                                    checked = isSelected,
                                    onCheckedChange = null
                                )
                            } else {
                                RadioButton(
                                    selected = isSelected,
                                    onClick = null
                                )
                            }
                            Text(text = option, modifier = Modifier.padding(start = 8.dp))
                        }
                    }
                    Divider(color = MaterialTheme.colorScheme.outlineVariant, thickness = 0.5.dp)
                }

                Spacer(modifier = Modifier.height(24.dp))

                if (isAnswerChecked) {
                    if (resultMessage != null) {
                        val isFullyCorrect = selectedOptionIndices == currentQuestion.correctIndices.toSet()
                        Text(
                            text = resultMessage ?: "",
                            style = MaterialTheme.typography.titleLarge,
                            color = if (isFullyCorrect) Color(0xFF4CAF50) else Color(0xFFF44336)
                        )
                        if (!isFullyCorrect) {
                            val correctLetters = currentQuestion.correctIndices.map { (it + 'A'.code).toChar() }.joinToString(", ")
                            Text(text = "Richtig wäre: $correctLetters", style = MaterialTheme.typography.bodyMedium, color = Color(0xFF4CAF50))
                        }
                        if (!currentQuestion.explanation.isNullOrEmpty()) {
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(text = "Erklärung: ${currentQuestion.explanation}", style = MaterialTheme.typography.bodyMedium)
                        }
                        Spacer(modifier = Modifier.height(16.dp))
                    }

                    // Only show "Nächste Frage" / "Ergebnis ansehen" if this is the current frontier question
                    if (!isViewingAnswered || currentQuestionIndex == questions.size - 1) {
                        Button(
                            onClick = {
                                if (currentQuestionIndex < questions.size - 1) {
                                    currentQuestionIndex++
                                } else {
                                    scope.launch {
                                        if (!isReviewMode) {
                                            repository.saveExamResult(examId, score, questions.size, true)
                                        }
                                        onFinished(score, questions.size)
                                    }
                                }
                            },
                            modifier = Modifier.fillMaxWidth().height(56.dp),
                            shape = MaterialTheme.shapes.medium
                        ) {
                            Text(if (currentQuestionIndex < questions.size - 1) "Nächste Frage" else "Ergebnis ansehen")
                        }
                    }
                } else {
                    Button(
                        onClick = {
                            if (selectedOptionIndices.isNotEmpty()) {
                                isAnswerChecked = true
                                val isCorrect = selectedOptionIndices == currentQuestion.correctIndices.toSet()
                                if (isCorrect) {
                                    score++
                                    resultMessage = "Richtig! Gut gemacht."
                                } else {
                                    resultMessage = "Leider nicht ganz richtig."
                                }
                                // Store in memory
                                answeredQuestions = answeredQuestions + (currentQuestionIndex to AnsweredQuestion(
                                    selectedIndices = selectedOptionIndices,
                                    isCorrect = isCorrect
                                ))
                                // Persist to DB
                                scope.launch {
                                    repository.saveQuestionResult(examId, currentQuestionIndex, isCorrect, selectedOptionIndices)
                                    if (!isReviewMode) {
                                        repository.saveExamResult(examId, score, questions.size, false)
                                    }
                                }
                            }
                        },
                        enabled = selectedOptionIndices.isNotEmpty(),
                        modifier = Modifier.fillMaxWidth().height(56.dp),
                        shape = MaterialTheme.shapes.medium
                    ) {
                        Text("Prüfen")
                    }
                }
            }
        } else {
            Text("Fehler: Frage nicht gefunden")
        }
    }
}
