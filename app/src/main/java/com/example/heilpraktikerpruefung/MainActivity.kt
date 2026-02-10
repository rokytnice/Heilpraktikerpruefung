package com.example.heilpraktikerpruefung

import android.os.Bundle
import android.content.Context
import android.content.res.Configuration
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import java.util.Locale


import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.example.heilpraktikerpruefung.ui.HomeScreen
import com.example.heilpraktikerpruefung.ui.QuizScreen
import com.example.heilpraktikerpruefung.ui.ResultScreen

class MainActivity : ComponentActivity() {
    override fun attachBaseContext(newBase: Context) {
        super.attachBaseContext(updateLocale(newBase))
    }
    
    private fun updateLocale(context: Context): Context {
        val locale = Locale("de", "DE")
        Locale.setDefault(locale)
        
        val config = Configuration(context.resources.configuration)
        config.setLocale(locale)
        
        return context.createConfigurationContext(config)
    }
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                 AppNavigation()
            }
        }
    }
}

@Composable
fun AppNavigation() {
    val navController = rememberNavController()
    NavHost(navController = navController, startDestination = "home") {
        composable("home") {
            HomeScreen(onExamClick = { examId ->
                navController.navigate("quiz/$examId")
            })
        }
        composable("quiz/{examId}") { backStackEntry ->
             val examId = backStackEntry.arguments?.getString("examId") ?: return@composable
             QuizScreen(examId = examId, onFinished = { score, total ->
                 navController.navigate("result/$examId/$score/$total") {
                     popUpTo("home") { inclusive = false }
                 }
             })
        }
        composable("result/{examId}/{score}/{total}") { backStackEntry ->
            val examId = backStackEntry.arguments?.getString("examId") ?: ""
            val score = backStackEntry.arguments?.getString("score")?.toIntOrNull() ?: 0
            val total = backStackEntry.arguments?.getString("total")?.toIntOrNull() ?: 0
            ResultScreen(
                examId = examId,
                score = score,
                totalQuestions = total,
                onHomeClick = {
                    navController.popBackStack("home", inclusive = false)
                },
                onRetryWrong = {
                    navController.navigate("quiz/REVIEW_$examId")
                }
            )
        }
    }
}

@Composable
fun Greeting(name: String, modifier: Modifier = Modifier) {
    Text(
        text = "Hello $name!",
        modifier = modifier
    )
}

@Preview(showBackground = true)
@Composable
fun GreetingPreview() {
    MaterialTheme {
        Greeting("Android")
    }
}
