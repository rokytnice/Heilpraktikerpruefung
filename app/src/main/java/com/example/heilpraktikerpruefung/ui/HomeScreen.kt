package com.example.heilpraktikerpruefung.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.unit.dp
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import com.example.heilpraktikerpruefung.data.Exam
import com.example.heilpraktikerpruefung.data.ExamRepository
import com.example.heilpraktikerpruefung.data.database.ExamResultEntity
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.runtime.getValue
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.Icons
import androidx.compose.ui.Alignment

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(onExamClick: (String) -> Unit) {
    val context = LocalContext.current
    val repository = remember { ExamRepository(context) }
    val exams = remember { repository.loadExams() }
    var examResults by remember { mutableStateOf<Map<String, ExamResultEntity>>(emptyMap()) }
    var examQuestionStats by remember { mutableStateOf<Map<String, Pair<Int, Int>>>(emptyMap()) } // examId -> (correct, total)
    var totalStats by remember { mutableStateOf<Pair<Int, Int>>(0 to 0) } // Correct to Total
    var hasWrongQuestions by remember { mutableStateOf(false) }

    // Refresh trigger: increments every time the screen resumes (navigated back to)
    var refreshTrigger by remember { mutableIntStateOf(0) }
    val lifecycleOwner = LocalLifecycleOwner.current
    DisposableEffect(lifecycleOwner) {
        val observer = LifecycleEventObserver { _, event ->
            if (event == Lifecycle.Event.ON_RESUME) {
                refreshTrigger++
            }
        }
        lifecycleOwner.lifecycle.addObserver(observer)
        onDispose { lifecycleOwner.lifecycle.removeObserver(observer) }
    }

    LaunchedEffect(refreshTrigger) {
        val results = repository.getAllExamResults()
        examResults = results.associateBy { it.examId }

        val allQuestionResults = repository.getAllQuestionResults()
        totalStats = allQuestionResults.count { it.isCorrect } to allQuestionResults.size
        hasWrongQuestions = allQuestionResults.any { !it.isCorrect }

        // Calculate question-level stats for each exam
        examQuestionStats = allQuestionResults
            .groupBy { it.examId }
            .mapValues { (_, questions) ->
                questions.count { it.isCorrect } to questions.size
            }
    }

    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(
                title = { 
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        androidx.compose.foundation.Image(
                            painter = androidx.compose.ui.res.painterResource(id = com.example.heilpraktikerpruefung.R.drawable.ic_launcher_foreground),
                            contentDescription = "Logo",
                            modifier = Modifier.size(40.dp)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("Heilpraktiker Prüfung", style = MaterialTheme.typography.titleLarge)
                    }
                },
                colors = TopAppBarDefaults.centerAlignedTopAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surfaceVariant
                )
            )
        }
    ) { paddingValues ->
        val groupedExams = remember(exams) { exams.groupBy { it.year }.toSortedMap(compareByDescending { it }) }
        val totalQuestions = remember(exams) { exams.sumOf { it.questions.size } }

        LazyColumn(
            contentPadding = PaddingValues(
                top = paddingValues.calculateTopPadding() + 16.dp,
                bottom = 16.dp,
                start = 16.dp,
                end = 16.dp
            ),
            modifier = Modifier.fillMaxSize()
        ) {
            item {
                StatsCard(
                    totalStats = totalStats,
                    totalQuestions = totalQuestions
                )
                Spacer(modifier = Modifier.height(24.dp))
                
                if (hasWrongQuestions) {
                    Button(
                        onClick = { onExamClick("REVIEW_ALL") },
                        modifier = Modifier.fillMaxWidth().height(56.dp),
                        shape = MaterialTheme.shapes.medium,
                        colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.errorContainer, contentColor = MaterialTheme.colorScheme.onErrorContainer)
                    ) {
                        Text("Fehlerschwerpunkte wiederholen", style = MaterialTheme.typography.titleMedium)
                    }
                    Spacer(modifier = Modifier.height(24.dp))
                }

                Text("Prüfungsarchiv", style = MaterialTheme.typography.headlineSmall)
                Spacer(modifier = Modifier.height(16.dp))
            }

            groupedExams.forEach { (year, examsInYear) ->
                item {
                    Text(
                        text = "$year",
                        style = MaterialTheme.typography.titleLarge,
                        color = MaterialTheme.colorScheme.primary,
                        modifier = Modifier.padding(vertical = 8.dp)
                    )
                }
                items(examsInYear.sortedByDescending { it.month }) { exam ->
                    val result = examResults[exam.id]
                    val questionStats = examQuestionStats[exam.id]
                    ExamItem(exam = exam, result = result, questionStats = questionStats, onClick = { onExamClick(exam.id) })
                    Spacer(modifier = Modifier.height(12.dp))
                }
                item { Spacer(modifier = Modifier.height(8.dp)) }
            }
        }
    }
}

@Composable
fun StatsCard(totalStats: Pair<Int, Int>, totalQuestions: Int) {
    val (correctQuestions, answeredQuestions) = totalStats
    
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = MaterialTheme.shapes.extraLarge,
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.secondaryContainer)
    ) {
        Column(modifier = Modifier.padding(20.dp)) {
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text(text = "Dein Fortschritt", style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.onSecondaryContainer)
                val progress = if (totalQuestions > 0) (answeredQuestions * 100) / totalQuestions else 0
                Text(text = "$progress%", style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.primary)
            }
            Spacer(modifier = Modifier.height(12.dp))
            LinearProgressIndicator(
                progress = if (totalQuestions > 0) answeredQuestions.toFloat() / totalQuestions else 0f,
                modifier = Modifier.fillMaxWidth().height(8.dp),
                strokeCap = StrokeCap.Round
            )
            Spacer(modifier = Modifier.height(16.dp))
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceEvenly) {
                StatItem("Fragen", "$answeredQuestions/$totalQuestions")
                val successRate = if (answeredQuestions > 0) (correctQuestions * 100) / answeredQuestions else 0
                StatItem("Erfolgsquote", "$successRate%")
            }
        }
    }
}

@Composable
fun StatItem(label: String, value: String) {
    Column(horizontalAlignment = androidx.compose.ui.Alignment.CenterHorizontally) {
        Text(text = value, style = MaterialTheme.typography.titleLarge, fontWeight = androidx.compose.ui.text.font.FontWeight.Bold)
        Text(text = label, style = MaterialTheme.typography.bodySmall)
    }
}

@Composable
fun ExamItem(exam: Exam, result: ExamResultEntity?, questionStats: Pair<Int, Int>?, onClick: () -> Unit) {
    // Determine which data source to use: questionStats (real-time) or result (completed exam)
    val (correctAnswers, totalAnswered) = when {
        questionStats != null -> questionStats
        result != null -> result.score to result.totalQuestions
        else -> 0 to 0
    }
    
    val hasProgress = totalAnswered > 0
    val totalQuestions = exam.questions.size
    
    Surface(
        onClick = onClick,
        shape = MaterialTheme.shapes.large,
        color = MaterialTheme.colorScheme.surface,
        tonalElevation = 2.dp,
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = androidx.compose.ui.Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Row(verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
                    Text(text = exam.month, style = MaterialTheme.typography.titleMedium)
                    
                    // Status badge - only show if exam has progress
                    if (hasProgress) {
                        Spacer(modifier = Modifier.width(8.dp))
                        val percentage = if (totalQuestions > 0) (correctAnswers * 100) / totalQuestions else 0
                        val isComplete = totalAnswered >= totalQuestions

                        val (badgeText, badgeColor) = when {
                            !isComplete -> "In Bearbeitung" to MaterialTheme.colorScheme.tertiary
                            percentage >= 75 -> "Bestanden" to MaterialTheme.colorScheme.primary
                            percentage >= 60 -> "Grenzwertig" to MaterialTheme.colorScheme.tertiary
                            else -> "Nicht bestanden" to MaterialTheme.colorScheme.error
                        }
                        
                        Surface(
                            shape = MaterialTheme.shapes.small,
                            color = badgeColor.copy(alpha = 0.15f)
                        ) {
                            Text(
                                text = badgeText,
                                style = MaterialTheme.typography.labelSmall,
                                color = badgeColor,
                                modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                            )
                        }
                    }
                }
                
                Row(verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
                    Text(
                        text = "$totalQuestions Fragen",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    
                    if (hasProgress) {
                        Text(
                            text = " • $correctAnswers/$totalAnswered richtig",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }
            
            if (hasProgress) {
                val percentage = if (totalQuestions > 0) (correctAnswers * 100) / totalQuestions else 0
                val color = when {
                    percentage >= 75 -> MaterialTheme.colorScheme.primary
                    percentage >= 60 -> MaterialTheme.colorScheme.tertiary
                    else -> MaterialTheme.colorScheme.error
                }
                
                Box(contentAlignment = androidx.compose.ui.Alignment.Center) {
                    CircularProgressIndicator(
                        progress = percentage.toFloat() / 100f,
                        modifier = Modifier.size(56.dp),
                        color = color,
                        trackColor = color.copy(alpha = 0.1f),
                        strokeWidth = 4.dp
                    )
                    Text(
                        text = "$percentage%",
                        style = MaterialTheme.typography.labelLarge,
                        fontWeight = androidx.compose.ui.text.font.FontWeight.Bold,
                        color = color
                    )
                }
            } else {
                Icon(
                    imageVector = androidx.compose.material.icons.Icons.Default.PlayArrow,
                    contentDescription = "Start",
                    tint = MaterialTheme.colorScheme.primary,
                    modifier = Modifier.size(32.dp)
                )
            }
        }
    }
}
