package com.example.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.BuildConfig
import com.example.data.FeedbackItem
import com.example.data.FeedbackRepository
import com.example.data.api.Content
import com.example.data.api.GeminiRequest
import com.example.data.api.GenerationConfig
import com.example.data.api.Part
import com.example.data.api.RetrofitClient
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

data class ChatMessage(
    val sender: MessageSender,
    val text: String,
    val timestamp: Long = System.currentTimeMillis()
)

enum class MessageSender {
    USER,
    BOT
}

class DiasporaViewModel : ViewModel() {

    // --- Feedback State ---
    val allItems: List<FeedbackItem> = FeedbackRepository.items

    private val _searchQuery = MutableStateFlow("")
    val searchQuery: StateFlow<String> = _searchQuery

    private val _selectedPlatform = MutableStateFlow<String?>(null)
    val selectedPlatform: StateFlow<String?> = _selectedPlatform

    private val _selectedSentiment = MutableStateFlow<String?>(null)
    val selectedSentiment: StateFlow<String?> = _selectedSentiment

    private val _selectedCity = MutableStateFlow<String?>(null)
    val selectedCity: StateFlow<String?> = _selectedCity

    val filteredItems: StateFlow<List<FeedbackItem>> = combine(
        _searchQuery,
        _selectedPlatform,
        _selectedSentiment,
        _selectedCity
    ) { query, platform, sentiment, city ->
        allItems.filter { item ->
            val matchesQuery = query.isEmpty() ||
                item.text.contains(query, ignoreCase = true) ||
                item.event.contains(query, ignoreCase = true) ||
                item.author.contains(query, ignoreCase = true)

            val matchesPlatform = platform == null || item.platform == platform
            val matchesSentiment = sentiment == null || item.sentiment == sentiment
            val matchesCity = city == null || item.city == city

            matchesQuery && matchesPlatform && matchesSentiment && matchesCity
        }
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), allItems)

    // --- Statistics ---
    val totalFeedbackCount: Int = allItems.size
    
    val sentimentPercentages: Map<String, Float> by lazy {
        val total = allItems.size.toFloat()
        if (total == 0f) emptyMap()
        else {
            val positives = allItems.count { it.sentiment == "Positive" }
            val neutrals = allItems.count { it.sentiment == "Neutral" }
            val negatives = allItems.count { it.sentiment == "Negative" }
            mapOf(
                "Positive" to (positives / total) * 100f,
                "Neutral" to (neutrals / total) * 100f,
                "Negative" to (negatives / total) * 100f
            )
        }
    }

    val platformCounts: Map<String, Int> by lazy {
        allItems.groupBy { it.platform }.mapValues { it.value.size }
    }

    val cityCounts: Map<String, Int> by lazy {
        allItems.groupBy { it.city }.mapValues { it.value.size }
    }

    // --- Chatbot State ---
    private val _chatMessages = MutableStateFlow<List<ChatMessage>>(
        listOf(
            ChatMessage(
                sender = MessageSender.BOT,
                text = "Hello! I am your RAG-enabled Diaspora Assistant. I have indexed all 2026 social media feedback from Twitter, Facebook, and Quora regarding Indian diaspora community events and upcoming activities in the Midlands. Ask me anything, or run sentiment / trend queries!"
            )
        )
    )
    val chatMessages: StateFlow<List<ChatMessage>> = _chatMessages

    private val _isChatLoading = MutableStateFlow(false)
    val isChatLoading: StateFlow<Boolean> = _isChatLoading

    private val _chatError = MutableStateFlow<String?>(null)
    val chatError: StateFlow<String?> = _chatError

    fun updateSearchQuery(query: String) {
        _searchQuery.value = query
    }

    fun selectPlatform(platform: String?) {
        _selectedPlatform.value = platform
    }

    fun selectSentiment(sentiment: String?) {
        _selectedSentiment.value = sentiment
    }

    fun selectCity(city: String?) {
        _selectedCity.value = city
    }

    fun clearFilters() {
        _selectedPlatform.value = null
        _selectedSentiment.value = null
        _selectedCity.value = null
        _searchQuery.value = ""
    }

    fun sendChatMessage(userText: String) {
        if (userText.trim().isEmpty() || _isChatLoading.value) return

        // 1. Add user message
        val updatedList = _chatMessages.value.toMutableList()
        updatedList.add(ChatMessage(sender = MessageSender.USER, text = userText))
        _chatMessages.value = updatedList

        _isChatLoading.value = true
        _chatError.value = null

        viewModelScope.launch {
            try {
                // Prepare RAG Context in system instructions
                val systemInstructionText = """
                    You are the "Diaspora RAG Bot", an expert sentiment analyzer and community reporter for the Indian Diaspora in the UK Midlands (including Birmingham, Leicester, Coventry, Wolverhampton, Nottingham, etc.).
                    
                    You have access to a consolidated database of social media feedback from Twitter (X), Facebook, and Quora regarding community event engagement in 2026, and upcoming planned events.
                    
                    Here is the entire consolidated dataset in Markdown format:
                    ${FeedbackRepository.getMarkdownSummary()}
                    
                    Instructions for your responses:
                    1. Answer the user's questions based strictly on the provided feedback dataset. Do not invent any posts, authors, or events that are not in the dataset.
                    2. If the user asks about sentiment, give an insightful analysis of Positive vs Neutral vs Negative feedback, highlighting specific complaints (e.g. Holi/Garba pricing, Vaisakhi crowd management, Sports Day rain delay) and achievements (e.g. Vaisakhi Langar quality, Sports Day youth engagement).
                    3. If asked about upcoming activities or planned events, detail the entries for Leicester Diwali Lights Switch-On 2026 (drone show, park and ride concerns) and Coventry Navratri Garba 2026 (scalping issues, new venue).
                    4. Keep your answers well-structured using markdown formatting (bullet points, bold text, headers) and highly professional. Speak with deep familiarity about Midlands UK geography.
                    5. If a query is outside the scope of community events, state: "I couldn't find specific social feedback on that in our consolidated 2026 Midlands database. However, based on our recorded trends..." and summarize the nearest relevant trend.
                """.trimIndent()

                // Map message history to Gemini API format (role user/model)
                val apiContents = updatedList.map { message ->
                    val roleName = if (message.sender == MessageSender.USER) "user" else "model"
                    Content(
                        parts = listOf(Part(text = message.text)),
                        role = roleName
                    )
                }

                // Call REST API using Retrofit
                val apiKey = BuildConfig.GEMINI_API_KEY
                if (apiKey.isEmpty() || apiKey == "MY_GEMINI_API_KEY") {
                    _chatMessages.value = _chatMessages.value + ChatMessage(
                        sender = MessageSender.BOT,
                        text = "⚠️ **API Key Missing**: It looks like your `GEMINI_API_KEY` is not set. Please open the **Secrets Panel in Google AI Studio** and enter your key there so I can perform live RAG analysis!\n\n*(Meanwhile, here is a quick overview: Holi tickets are seen as too expensive, Diwali drone plans are exciting but park-and-ride is requested, and Coventry Garba has ticket scalping issues.)*"
                    )
                    _isChatLoading.value = false
                    return@launch
                }

                val request = GeminiRequest(
                    contents = apiContents,
                    systemInstruction = Content(parts = listOf(Part(text = systemInstructionText))),
                    generationConfig = GenerationConfig(temperature = 0.3f)
                )

                val response = RetrofitClient.service.generateContent(apiKey, request)
                val botReplyText = response.candidates?.firstOrNull()?.content?.parts?.firstOrNull()?.text
                    ?: "I received an empty response. Please try rephrasing your question."

                _chatMessages.value = _chatMessages.value + ChatMessage(
                    sender = MessageSender.BOT,
                    text = botReplyText
                )

            } catch (e: Exception) {
                _chatError.value = "Failed to connect to AI server: ${e.localizedMessage ?: e.message}"
                _chatMessages.value = _chatMessages.value + ChatMessage(
                    sender = MessageSender.BOT,
                    text = "❌ **Error**: Could not connect to Gemini API. ${e.localizedMessage ?: "Please check your internet connection."}\n\n*Note: If the error persists, verify that the API key provided in the Secrets panel is valid.*"
                )
            } finally {
                _isChatLoading.value = false
            }
        }
    }
}
