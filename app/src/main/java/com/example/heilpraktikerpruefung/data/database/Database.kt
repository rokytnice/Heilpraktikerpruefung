package com.example.heilpraktikerpruefung.data.database

import androidx.room.Dao
import androidx.room.Database
import androidx.room.Entity
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.PrimaryKey
import androidx.room.Query
import androidx.room.RoomDatabase
import android.content.Context
import androidx.room.Room

@Entity(tableName = "exam_results")
data class ExamResultEntity(
    @PrimaryKey val examId: String,
    val score: Int,
    val totalQuestions: Int,
    val isFinished: Boolean,
    val lastUpdated: Long
)

@Entity(tableName = "question_results", primaryKeys = ["examId", "questionIndex"])
data class QuestionResultEntity(
    val examId: String,
    val questionIndex: Int,
    val isCorrect: Boolean,
    val timestamp: Long
)

@Dao
interface ExamDao {
    @Query("SELECT * FROM exam_results WHERE examId = :examId")
    suspend fun getExamResult(examId: String): ExamResultEntity?

    @Query("SELECT * FROM exam_results")
    suspend fun getAllExamResults(): List<ExamResultEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertExamResult(result: ExamResultEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertQuestionResult(result: QuestionResultEntity)

    @Query("SELECT * FROM question_results WHERE examId = :examId")
    suspend fun getQuestionResults(examId: String): List<QuestionResultEntity>

    @Query("SELECT * FROM question_results")
    suspend fun getAllQuestionResults(): List<QuestionResultEntity>

    @Query("SELECT * FROM question_results WHERE isCorrect = 0")
    suspend fun getAllWrongQuestionResults(): List<QuestionResultEntity>
}

@Database(entities = [ExamResultEntity::class, QuestionResultEntity::class], version = 1, exportSchema = false)
abstract class AppDatabase : RoomDatabase() {
    abstract fun examDao(): ExamDao

    companion object {
        @Volatile
        private var INSTANCE: AppDatabase? = null

        fun getDatabase(context: Context): AppDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    AppDatabase::class.java,
                    "hpp-database"
                ).build()
                INSTANCE = instance
                instance
            }
        }
    }
}
