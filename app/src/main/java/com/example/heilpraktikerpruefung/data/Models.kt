package com.example.heilpraktikerpruefung.data

import kotlinx.serialization.Serializable

@Serializable
data class Exam(
    val id: String,
    val year: Int,
    val month: String,
    val gruppe: String = "A",
    val questions: List<Question>
)

@Serializable
data class Question(
    val id: Int,
    val type: String, // "Einfachauswahl", "Mehrfachauswahl", "Aussagenkombination"
    val text: String,
    val options: List<String>,
    val statements: List<String> = emptyList(),
    val correctIndices: List<Int>,
    val explanation: String? = null
)
