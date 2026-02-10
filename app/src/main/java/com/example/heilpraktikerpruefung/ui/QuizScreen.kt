package com.example.heilpraktikerpruefung.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.verticalScroll
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

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun QuizScreen(examId: String, onFinished: (Int, Int) -> Unit) {
    val context = LocalContext.current
    val repository = remember { ExamRepository(context) }
    
    var questions by remember { mutableStateOf<List<Question>>(emptyList()) }
    var quizTitle by remember { mutableStateOf("Laden...") }
    var isLoading by remember { mutableStateOf(true) }

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
            }
        }
        isLoading = false
    }
    
    // State
    var currentQuestionIndex by remember { mutableIntStateOf(0) }
    var selectedOptionIndices by remember { mutableStateOf<Set<Int>>(emptySet()) }
    var resultMessage by remember { mutableStateOf<String?>(null) }
    var score by remember { mutableIntStateOf(0) }
    var isAnswerChecked by remember { mutableStateOf(false) }

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

    val scope = rememberCoroutineScope()

    Scaffold(
        topBar = {
            TopAppBar(title = { Text("$quizTitle - Frage ${currentQuestionIndex + 1}/${questions.size}") })
        }
    ) { paddingValues ->
        if (currentQuestion != null) {
            Column(
                modifier = Modifier
                    .padding(paddingValues)
                    .padding(16.dp)
                    .verticalScroll(rememberScrollState())
            ) {
                // ... (previous content)
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
                                    onCheckedChange = null // Handled by Row click
                                )
                            } else {
                                RadioButton(
                                    selected = isSelected,
                                    onClick = null // Handled by Row click
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
                             val correctLetters = currentQuestion.correctIndices.map { (it + 'A'.toInt()).toChar() }.joinToString(", ")
                             Text(text = "Richtig wäre: $correctLetters", style = MaterialTheme.typography.bodyMedium, color = Color(0xFF4CAF50))
                         }
                         if (currentQuestion.explanation != null && currentQuestion.explanation!!.isNotEmpty()) {
                             Spacer(modifier = Modifier.height(8.dp))
                             Text(text = "Erklärung: ${currentQuestion.explanation}", style = MaterialTheme.typography.bodyMedium)
                         }
                         Spacer(modifier = Modifier.height(16.dp))
                     }
                     
                    Button(
                        onClick = {
                            if (currentQuestionIndex < questions.size - 1) {
                                currentQuestionIndex++
                                selectedOptionIndices = emptySet()
                                isAnswerChecked = false
                                resultMessage = null
                            } else {
                                scope.launch {
                                    repository.saveExamResult(examId, score, questions.size, true)
                                    onFinished(score, questions.size)
                                }
                            }
                        },
                        modifier = Modifier.fillMaxWidth().height(56.dp),
                        shape = MaterialTheme.shapes.medium
                    ) {
                        Text(if (currentQuestionIndex < questions.size - 1) "Nächste Frage" else "Ergebnis ansehen")
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
                                scope.launch {
                                    repository.saveQuestionResult(examId, currentQuestionIndex, isCorrect)
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
            // Should not happen if index logic correct
            Text("Fehler: Frage nicht gefunden")
        }
    }
}
