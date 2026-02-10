package com.example.heilpraktikerpruefung.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.CenterAlignedTopAppBar
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.OutlinedButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ResultScreen(
    examId: String,
    score: Int,
    totalQuestions: Int,
    onHomeClick: () -> Unit,
    onRetryWrong: () -> Unit
) {
    val percentage = if (totalQuestions > 0) (score * 100) / totalQuestions else 0
    val isSuccess = percentage >= 75
    val feedbackColor = if (isSuccess) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.error

    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(title = { Text("Prüfungsergebnis") })
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(24.dp, Alignment.CenterVertically)
        ) {
            Text(
                text = if (isSuccess) "Bestanden!" else "Nicht bestanden",
                style = MaterialTheme.typography.headlineLarge,
                color = feedbackColor,
                fontWeight = androidx.compose.ui.text.font.FontWeight.Bold
            )

            Box(contentAlignment = Alignment.Center, modifier = Modifier.size(200.dp)) {
                CircularProgressIndicator(
                    progress = percentage.toFloat() / 100f,
                    modifier = Modifier.fillMaxSize(),
                    strokeWidth = 12.dp,
                    color = feedbackColor,
                    trackColor = feedbackColor.copy(alpha = 0.1f),
                    strokeCap = androidx.compose.ui.graphics.StrokeCap.Round
                )
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(text = "$percentage%", style = MaterialTheme.typography.displayMedium, fontWeight = androidx.compose.ui.text.font.FontWeight.ExtraBold)
                    Text(text = "$score von $totalQuestions", style = MaterialTheme.typography.titleMedium)
                }
            }

            Text(
                text = if (isSuccess) "Hervorragende Leistung! Du bist bereit für die nächste Herausforderung." 
                       else "Knapp daneben. Wiederhole die falschen Fragen, um deine Wissenslücken zu schließen.",
                style = MaterialTheme.typography.bodyLarge,
                textAlign = androidx.compose.ui.text.style.TextAlign.Center,
                modifier = Modifier.padding(horizontal = 16.dp)
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                if (score < totalQuestions) {
                    Button(
                        onClick = onRetryWrong, 
                        modifier = Modifier.fillMaxWidth().height(56.dp),
                        shape = MaterialTheme.shapes.medium,
                        colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.secondaryContainer, contentColor = MaterialTheme.colorScheme.onSecondaryContainer)
                    ) {
                        Text("Fehler wiederholen", style = MaterialTheme.typography.titleMedium)
                    }
                }
                
                OutlinedButton(
                    onClick = onHomeClick, 
                    modifier = Modifier.fillMaxWidth().height(56.dp),
                    shape = MaterialTheme.shapes.medium
                ) {
                    Text("Zurück zur Übersicht", style = MaterialTheme.typography.titleMedium)
                }
            }
        }
    }
}
