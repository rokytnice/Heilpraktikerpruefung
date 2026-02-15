package com.example.heilpraktikerpruefung.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.ArrowForward
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.outlined.Info
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.heilpraktikerpruefung.data.ExamRepository
import com.example.heilpraktikerpruefung.data.Question
import kotlinx.coroutines.launch

private data class AnsweredQuestion(
    val selectedIndices: Set<Int>,
    val isCorrect: Boolean
)

private fun assetExists(context: android.content.Context, path: String): Boolean {
    return try {
        context.assets.open(path).use { true }
    } catch (e: Exception) {
        false
    }
}

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

    // Image viewer state
    var showQuestionImageDialog by remember { mutableStateOf(false) }
    var showAnswerImageDialog by remember { mutableStateOf(false) }

    // Reset dialog state
    var showResetDialog by remember { mutableStateOf(false) }

    // Track source exam IDs and Gruppe for each question (needed for REVIEW_ALL mode)
    var questionExamIds by remember { mutableStateOf<List<String>>(emptyList()) }
    var questionGruppen by remember { mutableStateOf<List<String>>(emptyList()) }

    val scope = rememberCoroutineScope()

    LaunchedEffect(examId) {
        if (examId == "REVIEW_ALL") {
            val wrongPairs = repository.getWrongQuestions()
            val loadedQuestions = mutableListOf<Question>()
            val loadedExamIds = mutableListOf<String>()
            val loadedGruppen = mutableListOf<String>()
            for ((eId, qIdx) in wrongPairs) {
                val q = repository.getQuestion(eId, qIdx)
                if (q != null) {
                    loadedQuestions.add(q)
                    loadedExamIds.add(eId)
                    loadedGruppen.add(repository.getGruppe(eId))
                }
            }
            questions = loadedQuestions
            questionExamIds = loadedExamIds
            questionGruppen = loadedGruppen
            quizTitle = "Wiederholung: Alle Falschen"
        } else if (examId.startsWith("REVIEW_")) {
            val actualExamId = examId.removePrefix("REVIEW_")
            val results = repository.getQuestionResults(actualExamId)
            val loadedQuestions = mutableListOf<Question>()
            val loadedExamIds = mutableListOf<String>()
            val gruppe = repository.getGruppe(actualExamId)
            for (qr in results.filter { !it.isCorrect }) {
                val q = repository.getQuestion(actualExamId, qr.questionIndex)
                if (q != null) {
                    loadedQuestions.add(q)
                    loadedExamIds.add(actualExamId)
                }
            }
            questions = loadedQuestions
            questionExamIds = loadedExamIds
            questionGruppen = List(loadedQuestions.size) { gruppe }
            quizTitle = "Wiederholung: $actualExamId"
        } else {
            val exam = repository.getExamById(examId)
            if (exam != null) {
                questions = exam.questions
                questionExamIds = List(exam.questions.size) { examId }
                questionGruppen = List(exam.questions.size) { exam.gruppe }
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

    // Determine exam ID and Gruppe for current question's images
    val currentExamIdForImages = questionExamIds.getOrNull(currentQuestionIndex) ?: ""
    val currentGruppe = questionGruppen.getOrNull(currentQuestionIndex) ?: "A"
    val questionImagePath = "images/$currentExamIdForImages/q${currentQuestion?.id}.webp"
    val answerImagePath = "images/$currentExamIdForImages/answer_key.webp"
    val hasQuestionImage = remember(questionImagePath) { assetExists(context, questionImagePath) }
    val hasAnswerImage = remember(answerImagePath) { assetExists(context, answerImagePath) }

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

    // Image viewer dialogs
    if (showQuestionImageDialog && hasQuestionImage) {
        ImageViewerDialog(
            assetPath = questionImagePath,
            title = "Originalfrage ${currentQuestion?.id}",
            onDismiss = { showQuestionImageDialog = false }
        )
    }
    if (showAnswerImageDialog && hasAnswerImage) {
        ImageViewerDialog(
            assetPath = answerImagePath,
            title = "Lösungsschlüssel Gruppe $currentGruppe",
            onDismiss = { showAnswerImageDialog = false }
        )
    }

    if (showResetDialog) {
        AlertDialog(
            onDismissRequest = { showResetDialog = false },
            title = { Text("Fortschritt zurücksetzen?") },
            text = { Text("Alle Antworten dieser Prüfung werden gelöscht und du startest von vorne.") },
            confirmButton = {
                TextButton(onClick = {
                    showResetDialog = false
                    scope.launch {
                        repository.deleteQuestionResults(examId)
                    }
                    // Reset all in-memory state
                    answeredQuestions = emptyMap()
                    currentQuestionIndex = 0
                    selectedOptionIndices = emptySet()
                    isAnswerChecked = false
                    resultMessage = null
                    score = 0
                }) {
                    Text("Zurücksetzen")
                }
            },
            dismissButton = {
                TextButton(onClick = { showResetDialog = false }) {
                    Text("Abbrechen")
                }
            }
        )
    }

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
                    IconButton(onClick = { showResetDialog = true }) {
                        Icon(Icons.Default.Refresh, contentDescription = "Zurücksetzen")
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
                // Question text + image buttons row
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.Top
                ) {
                    Text(
                        text = currentQuestion.text,
                        style = MaterialTheme.typography.bodyLarge,
                        modifier = Modifier.weight(1f)
                    )
                    if (hasQuestionImage || hasAnswerImage) {
                        Column {
                            if (hasQuestionImage) {
                                IconButton(
                                    onClick = { showQuestionImageDialog = true },
                                    modifier = Modifier.size(36.dp)
                                ) {
                                    Icon(
                                        Icons.Outlined.Info,
                                        contentDescription = "Originalfrage anzeigen",
                                        tint = MaterialTheme.colorScheme.primary
                                    )
                                }
                            }
                            if (hasAnswerImage) {
                                IconButton(
                                    onClick = { showAnswerImageDialog = true },
                                    modifier = Modifier.size(36.dp)
                                ) {
                                    Text(
                                        currentGruppe,
                                        fontWeight = FontWeight.Bold,
                                        fontSize = 16.sp,
                                        color = MaterialTheme.colorScheme.primary
                                    )
                                }
                            }
                        }
                    }
                }
                Spacer(modifier = Modifier.height(16.dp))

                if (currentQuestion.statements.isNotEmpty()) {
                    Text(text = "Aussagen:", style = MaterialTheme.typography.bodyLarge)
                    currentQuestion.statements.forEachIndexed { index, statement ->
                        Text(
                            text = "${index + 1}. $statement",
                            style = MaterialTheme.typography.bodyLarge,
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
                            Text(text = option, style = MaterialTheme.typography.bodyLarge, modifier = Modifier.padding(start = 8.dp))
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
                            Text(text = "Richtig wäre: $correctLetters", style = MaterialTheme.typography.bodyLarge, color = Color(0xFF4CAF50))
                        }
                        if (!currentQuestion.explanation.isNullOrEmpty()) {
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(text = "Erklärung: ${currentQuestion.explanation}", style = MaterialTheme.typography.bodyLarge)
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
