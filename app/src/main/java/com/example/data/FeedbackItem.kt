package com.example.data

data class FeedbackItem(
    val id: String,
    val platform: String, // "Twitter" | "Facebook" | "Quora"
    val author: String,
    val date: String,
    val event: String,
    val text: String,
    val sentiment: String, // "Positive" | "Neutral" | "Negative"
    val city: String,
    val isUpcoming: Boolean = false
)
