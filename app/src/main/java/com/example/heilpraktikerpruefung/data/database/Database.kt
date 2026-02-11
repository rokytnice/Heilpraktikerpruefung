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
import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase

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
    val timestamp: Long,
    val selectedIndices: String = ""
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

    @Query("DELETE FROM question_results WHERE examId = :examId")
    suspend fun deleteQuestionResults(examId: String)

    @Query("DELETE FROM exam_results WHERE examId = :examId")
    suspend fun deleteExamResult(examId: String)
}

val MIGRATION_1_2 = object : Migration(1, 2) {
    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL("ALTER TABLE question_results ADD COLUMN selectedIndices TEXT NOT NULL DEFAULT ''")
    }
}

@Database(entities = [ExamResultEntity::class, QuestionResultEntity::class], version = 2, exportSchema = false)
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
                )
                    .addMigrations(MIGRATION_1_2)
                    .build()
                INSTANCE = instance
                instance
            }
        }
    }
}
