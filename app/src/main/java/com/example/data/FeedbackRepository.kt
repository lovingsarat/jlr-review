package com.example.data

object FeedbackRepository {
    val items: List<FeedbackItem> = listOf(
        FeedbackItem(
            id = "1",
            platform = "Twitter",
            author = "@AmitBrum",
            date = "2026-03-22",
            event = "Midlands Holi Festival 2026",
            text = "The Birmingham Holi Festival 2026 was absolutely spectacular! Incredible colors, lively dhol players, and such an amazing atmosphere at Ward End Park. The Midlands diaspora really showed up today! 🇮🇳✨",
            sentiment = "Positive",
            city = "Birmingham"
        ),
        FeedbackItem(
            id = "2",
            platform = "Facebook",
            author = "Preeti Patel",
            date = "2026-03-23",
            event = "Midlands Holi Festival 2026",
            text = "Extremely frustrated with the ticket prices for the Midlands Holi event. £25 per person is way too steep for families. Also, the queue for the food stalls was over an hour long! Kids were starving.",
            sentiment = "Negative",
            city = "Birmingham"
        ),
        FeedbackItem(
            id = "3",
            platform = "Quora",
            author = "Rajan Sharma",
            date = "2026-03-24",
            event = "Midlands Holi Festival 2026",
            text = "Attended the Holi festival in Birmingham last weekend. While the cultural performances were top-notch and the community spirit was strong, the parking situation was a total mess and there weren't enough washroom facilities for the crowd.",
            sentiment = "Neutral",
            city = "Birmingham"
        ),
        FeedbackItem(
            id = "4",
            platform = "Twitter",
            author = "@Leicester_Sunita",
            date = "2026-04-19",
            event = "Birmingham Vaisakhi Mela 2026",
            text = "So glad we made the trip from Leicester to Handsworth Park for Vaisakhi Mela 2026! The Langar (free kitchen) was served with so much love, and the energetic Bhangra acts had everyone dancing. Wonderful community engagement!",
            sentiment = "Positive",
            city = "Birmingham"
        ),
        FeedbackItem(
            id = "5",
            platform = "Facebook",
            author = "Gurpreet Singh",
            date = "2026-04-20",
            event = "Birmingham Vaisakhi Mela 2026",
            text = "The crowd management at the Handsworth Park Vaisakhi event was quite poor. It felt unsafe at times around the main stage area, and there was litter everywhere by 4 PM. We really need more waste bins and volunteers next year.",
            sentiment = "Negative",
            city = "Birmingham"
        ),
        FeedbackItem(
            id = "6",
            platform = "Twitter",
            author = "@MidlandsIndSoc",
            date = "2026-06-14",
            event = "Midlands Indian Sports Day 2026",
            text = "Huge congratulations to the organizers of the Indian Sports Day in Leicester! Seeing the youngsters play Kabaddi and Kho-Kho was pure nostalgia. Wonderful initiative to keep our cultural sports alive in the UK Midlands.",
            sentiment = "Positive",
            city = "Leicester"
        ),
        FeedbackItem(
            id = "7",
            platform = "Facebook",
            author = "Vikram Rao",
            date = "2026-06-15",
            event = "Midlands Indian Sports Day 2026",
            text = "Great concept, but the execution of the Sports Day was ruined by the typical British summer rain. There was no indoor backup plan for most matches, and the scheduling was delayed by 3 hours. Please plan better for wet weather in 2026!",
            sentiment = "Negative",
            city = "Leicester"
        ),
        FeedbackItem(
            id = "8",
            platform = "Quora",
            author = "Anjali Desai",
            date = "2026-07-02",
            event = "Leicester Diwali Lights Switch-On 2026",
            text = "What are the upcoming planned activities for the Leicester Diwali Lights Switch-On in October 2026? I heard they are introducing a massive drone light show on Belgrave Road this year instead of traditional fireworks. Is this true?",
            sentiment = "Neutral",
            city = "Leicester",
            isUpcoming = true
        ),
        FeedbackItem(
            id = "9",
            platform = "Twitter",
            author = "@CoventryDesis",
            date = "2026-07-10",
            event = "Leicester Diwali Lights Switch-On 2026",
            text = "So excited for the upcoming Diwali Lights Switch-On 2026 in Leicester! The drone light show sounds brilliant and eco-friendly. Leicester Belgrave Road is the place to be this autumn. Already planning our family get-together!",
            sentiment = "Positive",
            city = "Leicester",
            isUpcoming = true
        ),
        FeedbackItem(
            id = "10",
            platform = "Facebook",
            author = "Neha Shah",
            date = "2026-07-12",
            event = "Leicester Diwali Lights Switch-On 2026",
            text = "While the drone show sounds exciting for Diwali 2026, I am really worried about Belgrave Road traffic closures. Parking in Leicester during Diwali is already impossible. The council needs to provide park-and-ride shuttle buses.",
            sentiment = "Neutral",
            city = "Leicester",
            isUpcoming = true
        ),
        FeedbackItem(
            id = "11",
            platform = "Twitter",
            author = "@GarbaCoventry",
            date = "2026-07-11",
            event = "Coventry Navratri Garba 2026",
            text = "Navratri Garba tickets in Coventry sold out in literally 10 minutes! 😡 Now scalpers are reselling £12 tickets for £45 on Facebook groups. This is unfair to genuine community members who want to celebrate. Organizers need a better ticketing system!",
            sentiment = "Negative",
            city = "Coventry",
            isUpcoming = true
        ),
        FeedbackItem(
            id = "12",
            platform = "Facebook",
            author = "Meera Joshi",
            date = "2026-07-13",
            event = "Coventry Navratri Garba 2026",
            text = "Thrilled that Navratri Garba 2026 is moving to a larger venue in Coventry! The community has grown so fast in the West Midlands. This year is going to be magnificent with live musicians flying in from Gujarat. Can't wait!",
            sentiment = "Positive",
            city = "Coventry",
            isUpcoming = true
        ),
        FeedbackItem(
            id = "13",
            platform = "Quora",
            author = "Devendra Patel",
            date = "2026-05-10",
            event = "Midlands Indian Food Festival 2026",
            text = "Which was the best Indian food event in the Midlands in 2026? Hands down the Midlands Indian Food Festival in Birmingham. The street food variety was mind-blowing – everything from Lucknowi chaat to South Indian filter coffee. Extremely well organized!",
            sentiment = "Positive",
            city = "Birmingham"
        ),
        FeedbackItem(
            id = "14",
            platform = "Twitter",
            author = "@BrumFoodie",
            date = "2026-05-11",
            event = "Midlands Indian Food Festival 2026",
            text = "The Birmingham food festival had excellent culinary representation, but the venue (Digbeth Arena) was extremely cramped. Long lines made it hard to walk around. They should move it to a larger park area next year.",
            sentiment = "Neutral",
            city = "Birmingham"
        ),
        FeedbackItem(
            id = "15",
            platform = "Quora",
            author = "Rohan Kapoor",
            date = "2026-07-05",
            event = "General Community Feedback 2026",
            text = "The level of Indian diaspora community engagement in the East Midlands (Nottingham, Leicester) has spiked in 2026. The youth-led cultural societies are doing a fantastic job bridging generational gaps through regional festivals and sports.",
            sentiment = "Positive",
            city = "Nottingham"
        )
    )

    fun getMarkdownSummary(): String {
        val sb = java.lang.StringBuilder()
        sb.append("| Platform | Author | Date | Event | Sentiment | City | Feedback text |\n")
        sb.append("| --- | --- | --- | --- | --- | --- | --- |\n")
        items.forEach { item ->
            val upcomingTag = if (item.isUpcoming) " (Upcoming Planned Activity)" else ""
            sb.append("| ${item.platform} | ${item.author} | ${item.date} | ${item.event}$upcomingTag | ${item.sentiment} | ${item.city} | ${item.text.replace("|", "\\|")} |\n")
        }
        return sb.toString()
    }
}
