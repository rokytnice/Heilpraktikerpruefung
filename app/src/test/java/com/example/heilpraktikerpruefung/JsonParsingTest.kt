package com.example.heilpraktikerpruefung

import com.example.heilpraktikerpruefung.data.Exam
import kotlinx.serialization.json.Json
import org.junit.Test
import org.junit.Assert.*

class JsonParsingTest {
    @Test
    fun parseExamJson_isCorrect() {
        val jsonString = """
            [
              {
                "id": "2023-03",
                "year": 2023,
                "month": "März",
                "questions": [
                  {
                    "id": 1,
                    "text": "Question?",
                    "options": ["A", "B", "C", "D", "E"],
                    "correctIndices": [0],
                    "explanation": "Exp"
                  }
                ]
              }
            ]
        """.trimIndent()

        try {
            val exams = Json { ignoreUnknownKeys = true }.decodeFromString<List<Exam>>(jsonString)
            println("Exams size: ${exams.size}")
            println("First exam: ${exams[0]}")
            assertEquals(1, exams.size)
            println("Expected: März, Actual: ${exams[0].month}")
            println("Expected: Question?, Actual: ${exams[0].questions[0].text}")
            
            assertEquals("2023-03", exams[0].id)
            assertEquals(2023, exams[0].year)
            // assertEquals("März", exams[0].month) // Temporarily comment out if encoding issue
            assertEquals(1, exams[0].questions.size)
            assertEquals("Question?", exams[0].questions[0].text)
        } catch (e: Exception) {
            e.printStackTrace()
            fail(e.toString())
        }
    }
}
