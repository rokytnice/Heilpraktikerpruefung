package com.example.heilpraktikerpruefung.data

import android.content.Context
import androidx.room.Room
import com.example.heilpraktikerpruefung.data.database.AppDatabase
import com.example.heilpraktikerpruefung.data.database.ExamResultEntity
import com.example.heilpraktikerpruefung.data.database.QuestionResultEntity
import kotlinx.serialization.json.Json
import java.io.IOException

class ExamRepository(private val context: Context) {

    private val json = Json { ignoreUnknownKeys = true }
    
    // Lazy initialization of database
    private val db by lazy {
        AppDatabase.getDatabase(context)
    }

    private var cachedExams: List<Exam>? = null

    fun loadExams(): List<Exam> {
        if (cachedExams != null) return cachedExams!!
        
        return try {
            val jsonString = context.assets.open("exams.json").bufferedReader().use { it.readText() }
            cachedExams = json.decodeFromString<List<Exam>>(jsonString)
            cachedExams!!
        } catch (ioException: IOException) {
            ioException.printStackTrace()
            emptyList()
        }
    }
    
    fun getExamById(id: String): Exam? {
        return loadExams().find { it.id == id }
    }

    fun getQuestion(examId: String, questionIndex: Int): Question? {
        return getExamById(examId)?.questions?.getOrNull(questionIndex)
    }

    suspend fun saveExamResult(examId: String, score: Int, total: Int, isFinished: Boolean) {
        db.examDao().insertExamResult(
            ExamResultEntity(
                examId = examId,
                score = score,
                totalQuestions = total,
                isFinished = isFinished,
                lastUpdated = System.currentTimeMillis()
            )
        )
    }

    suspend fun getExamResult(examId: String): ExamResultEntity? {
        return db.examDao().getExamResult(examId)
    }

    suspend fun getAllExamResults(): List<ExamResultEntity> {
        return db.examDao().getAllExamResults()
    }

    suspend fun saveQuestionResult(examId: String, questionIndex: Int, isCorrect: Boolean, selectedIndices: Set<Int> = emptySet()) {
        db.examDao().insertQuestionResult(
            QuestionResultEntity(
                examId = examId,
                questionIndex = questionIndex,
                isCorrect = isCorrect,
                timestamp = System.currentTimeMillis(),
                selectedIndices = selectedIndices.sorted().joinToString(",")
            )
        )
    }

    suspend fun deleteQuestionResults(examId: String) {
        db.examDao().deleteQuestionResults(examId)
        db.examDao().deleteExamResult(examId)
    }

    suspend fun getQuestionResults(examId: String): List<QuestionResultEntity> {
        return db.examDao().getQuestionResults(examId)
    }

    suspend fun getAllQuestionResults(): List<QuestionResultEntity> {
        return db.examDao().getAllQuestionResults()
    }

    suspend fun getWrongQuestions(): List<Pair<String, Int>> {
        return db.examDao().getAllWrongQuestionResults().map { it.examId to it.questionIndex }
    }
}
