package com.example.ui

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.Send
import androidx.compose.material.icons.filled.Chat
import androidx.compose.material.icons.filled.Clear
import androidx.compose.material.icons.filled.Dashboard
import androidx.compose.material.icons.filled.Event
import androidx.compose.material.icons.filled.Explore
import androidx.compose.material.icons.filled.Forum
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.LocationOn
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.TrendingUp
import androidx.compose.material3.Badge
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.ScrollableTabRow
import androidx.compose.material3.Tab
import androidx.compose.material3.TabRowDefaults
import androidx.compose.material3.TabRowDefaults.tabIndicatorOffset
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.data.FeedbackItem
import kotlin.math.roundToInt

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DiasporaHubApp(viewModel: DiasporaViewModel) {
    var selectedTab by remember { mutableIntStateOf(0) }
    val tabs = listOf("Dashboard", "AI RAG Chat", "Feed Explorer")

    Scaffold(
        modifier = Modifier.fillMaxSize(),
        topBar = {
            TopAppBar(
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.background,
                    titleContentColor = MaterialTheme.colorScheme.onBackground
                ),
                title = {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        // Material 3 style circular avatar from Professional Polish HTML
                        Box(
                            modifier = Modifier
                                .size(40.dp)
                                .clip(CircleShape)
                                .background(MaterialTheme.colorScheme.primary),
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                text = "DP",
                                color = Color.White,
                                fontSize = 16.sp,
                                fontWeight = FontWeight.Bold
                            )
                        }
                        Column {
                            Text(
                                text = "Midlands Pulse '26",
                                fontWeight = FontWeight.SemiBold,
                                fontSize = 18.sp,
                                fontFamily = FontFamily.SansSerif,
                                modifier = Modifier.testTag("app_title_text")
                            )
                            Text(
                                text = "INDIAN DIASPORA ENGAGEMENT",
                                fontSize = 9.sp,
                                fontWeight = FontWeight.Bold,
                                letterSpacing = 0.5.sp,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }
                },
                actions = {
                    // Quick clear filters option
                    IconButton(
                        onClick = { viewModel.clearFilters() },
                        modifier = Modifier.testTag("reset_filters_appbar")
                    ) {
                        Icon(
                            imageVector = Icons.Default.Refresh,
                            contentDescription = "Reset Filters",
                            tint = MaterialTheme.colorScheme.primary
                        )
                    }
                }
            )
        }
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .background(MaterialTheme.colorScheme.background)
        ) {
            // Elegant styled TabRow with deep custom brand line
            ScrollableTabRow(
                selectedTabIndex = selectedTab,
                containerColor = MaterialTheme.colorScheme.background,
                contentColor = MaterialTheme.colorScheme.primary,
                edgePadding = 16.dp,
                indicator = { tabPositions ->
                    TabRowDefaults.SecondaryIndicator(
                        Modifier.tabIndicatorOffset(tabPositions[selectedTab]),
                        color = MaterialTheme.colorScheme.primary,
                        height = 3.dp
                    )
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .testTag("main_navigation_tab_row")
            ) {
                tabs.forEachIndexed { index, title ->
                    Tab(
                        selected = selectedTab == index,
                        onClick = { selectedTab = index },
                        text = {
                            Text(
                                text = title,
                                fontWeight = if (selectedTab == index) FontWeight.Bold else FontWeight.Medium,
                                fontSize = 14.sp,
                                color = if (selectedTab == index) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        },
                        icon = {
                            when (index) {
                                0 -> Icon(Icons.Default.Dashboard, contentDescription = null, modifier = Modifier.size(20.dp))
                                1 -> Icon(Icons.Default.Chat, contentDescription = null, modifier = Modifier.size(20.dp))
                                2 -> Icon(Icons.Default.Explore, contentDescription = null, modifier = Modifier.size(20.dp))
                            }
                        }
                    )
                }
            }

            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .weight(1f)
            ) {
                when (selectedTab) {
                    0 -> DashboardTab(viewModel)
                    1 -> ChatTab(viewModel)
                    2 -> ExplorerTab(viewModel)
                }
            }
        }
    }
}

@Composable
fun DashboardTab(viewModel: DiasporaViewModel) {
    val items = viewModel.allItems

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .testTag("dashboard_tab_content"),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // --- 1. Hero Welcoming Announcement Banner ---
        item {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(24.dp))
                    .drawBehind {
                        drawRect(
                            brush = Brush.radialGradient(
                                colors = listOf(Color(0xFFEADDFF).copy(alpha = 0.4f), Color(0xFFF7F2FA)),
                                center = Offset(size.width * 0.8f, 0f),
                                radius = size.width * 1.2f
                            )
                        )
                    }
                    .background(Color(0xFFFFFFFF))
                    .clickable { }
                    .padding(20.dp)
            ) {
                Column(
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Badge(
                            containerColor = MaterialTheme.colorScheme.primaryContainer,
                            contentColor = MaterialTheme.colorScheme.onPrimaryContainer,
                            modifier = Modifier.padding(bottom = 8.dp)
                        ) {
                            Text(
                                text = "2026 CONSOLIDATED SUMMARY",
                                fontWeight = FontWeight.Bold,
                                fontSize = 10.sp,
                                modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                            )
                        }

                        Text(text = "🇮🇳", fontSize = 24.sp)
                    }

                    Text(
                        text = "Midlands Indian Diaspora Community Event Feedback",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Black,
                        color = MaterialTheme.colorScheme.primary,
                        lineHeight = 22.sp
                    )

                    Spacer(modifier = Modifier.height(4.dp))

                    Text(
                        text = "Aggregated data from Twitter (X), Facebook groups, and Quora spaces tracking community event engagement and upcoming planned activities across the region.",
                        fontSize = 12.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        }

        // --- 2. KPI Row: Material 3 Cards ---
        item {
            val percentages = viewModel.sentimentPercentages
            val positivePct = (percentages["Positive"] ?: 84f).roundToInt()
            val mentions = "12.4k" // Matching the requested design value
            
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                // Sentiment card: PrimaryContainer (#EADDFF)
                Card(
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.primaryContainer,
                        contentColor = MaterialTheme.colorScheme.onPrimaryContainer
                    ),
                    shape = RoundedCornerShape(20.dp),
                    elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
                    modifier = Modifier.weight(1f)
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(12.dp),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center
                    ) {
                        Text(
                            text = "Sentiment",
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Medium
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = "$positivePct%",
                            fontSize = 20.sp,
                            fontWeight = FontWeight.Bold
                        )
                        Spacer(modifier = Modifier.height(2.dp))
                        Text(
                            text = "POSITIVE",
                            fontSize = 8.sp,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.7f)
                        )
                    }
                }

                // Mentions card: SecondaryContainer (#D0E4FF)
                Card(
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.secondaryContainer,
                        contentColor = MaterialTheme.colorScheme.onSecondaryContainer
                    ),
                    shape = RoundedCornerShape(20.dp),
                    elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
                    modifier = Modifier.weight(1f)
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(12.dp),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center
                    ) {
                        Text(
                            text = "Mentions",
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Medium
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = mentions,
                            fontSize = 20.sp,
                            fontWeight = FontWeight.Bold
                        )
                        Spacer(modifier = Modifier.height(2.dp))
                        Text(
                            text = "SOCIAL AGG",
                            fontSize = 8.sp,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.onSecondaryContainer.copy(alpha = 0.7f)
                        )
                    }
                }

                // Events card: TertiaryContainer (#F3E8FF)
                Card(
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.tertiaryContainer,
                        contentColor = MaterialTheme.colorScheme.onTertiaryContainer
                    ),
                    shape = RoundedCornerShape(20.dp),
                    elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
                    modifier = Modifier.weight(1f)
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(12.dp),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center
                    ) {
                        Text(
                            text = "Events",
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Medium
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = "18", // Matching design HTML events KPI count
                            fontSize = 20.sp,
                            fontWeight = FontWeight.Bold
                        )
                        Spacer(modifier = Modifier.height(2.dp))
                        Text(
                            text = "UPCOMING '26",
                            fontSize = 8.sp,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.onTertiaryContainer.copy(alpha = 0.7f)
                        )
                    }
                }
            }
        }

        // --- 2. Sentiment Metrics Canvas Chart (Interactive Donut) ---
        item {
            Card(
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                shape = RoundedCornerShape(16.dp),
                elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp)
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Default.TrendingUp,
                            contentDescription = null,
                            tint = MaterialTheme.colorScheme.primary
                        )
                        Text(
                            text = "Sentiment Breakdown Analysis",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold
                        )
                    }

                    Spacer(modifier = Modifier.height(16.dp))

                    // Draw dynamic Donut chart with Canvas
                    val percentages = viewModel.sentimentPercentages
                    val positivePct = percentages["Positive"] ?: 0f
                    val neutralPct = percentages["Neutral"] ?: 0f
                    val negativePct = percentages["Negative"] ?: 0f

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Box(
                            contentAlignment = Alignment.Center,
                            modifier = Modifier
                                .size(130.dp)
                                .weight(1f)
                        ) {
                            Canvas(modifier = Modifier.size(100.dp)) {
                                val strokeWidth = 35f
                                var startAngle = -90f

                                // Positive Arc (Green)
                                val sweepPositive = (positivePct / 100f) * 360f
                                drawArc(
                                    color = Color(0xFF2E7D32),
                                    startAngle = startAngle,
                                    sweepAngle = sweepPositive,
                                    useCenter = false,
                                    style = Stroke(width = strokeWidth, cap = StrokeCap.Round)
                                )
                                startAngle += sweepPositive

                                // Neutral Arc (Orange-Gold)
                                val sweepNeutral = (neutralPct / 100f) * 360f
                                drawArc(
                                    color = Color(0xFFF9A825),
                                    startAngle = startAngle,
                                    sweepAngle = sweepNeutral,
                                    useCenter = false,
                                    style = Stroke(width = strokeWidth, cap = StrokeCap.Round)
                                )
                                startAngle += sweepNeutral

                                // Negative Arc (Crimson)
                                val sweepNegative = (negativePct / 100f) * 360f
                                drawArc(
                                    color = Color(0xFFC62828),
                                    startAngle = startAngle,
                                    sweepAngle = sweepNegative,
                                    useCenter = false,
                                    style = Stroke(width = strokeWidth, cap = StrokeCap.Round)
                                )
                            }
                            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                Text(
                                    text = "${positivePct.roundToInt()}%",
                                    fontSize = 18.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = Color(0xFF2E7D32)
                                )
                                Text(
                                    text = "Positive",
                                    fontSize = 9.sp,
                                    color = Color.Gray,
                                    fontWeight = FontWeight.Bold
                                )
                            }
                        }

                        // Chart Legend with specific counts
                        Column(
                            modifier = Modifier
                                .weight(1.2f)
                                .padding(start = 12.dp),
                            verticalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            SentimentLegendItem(
                                label = "Positive Review",
                                percentage = positivePct,
                                count = items.count { it.sentiment == "Positive" },
                                color = Color(0xFF2E7D32)
                            )
                            SentimentLegendItem(
                                label = "Neutral Comments",
                                percentage = neutralPct,
                                count = items.count { it.sentiment == "Neutral" },
                                color = Color(0xFFF9A825)
                            )
                            SentimentLegendItem(
                                label = "Negative Feedback",
                                percentage = negativePct,
                                count = items.count { it.sentiment == "Negative" },
                                color = Color(0xFFC62828)
                            )
                        }
                    }
                }
            }
        }

        // --- 3. Platforms & Regions Split Grid ---
        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                // Platform count card
                Card(
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                    shape = RoundedCornerShape(16.dp),
                    elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
                    modifier = Modifier.weight(1f)
                ) {
                    Column(
                        modifier = Modifier.padding(14.dp)
                    ) {
                        Text(
                            text = "Platform Feed",
                            fontWeight = FontWeight.Bold,
                            fontSize = 12.sp,
                            color = MaterialTheme.colorScheme.primary
                        )
                        Spacer(modifier = Modifier.height(10.dp))

                        val platformCounts = viewModel.platformCounts
                        PlatformBar("Twitter", platformCounts["Twitter"] ?: 0, 15, Color(0xFF1DA1F2))
                        Spacer(modifier = Modifier.height(8.dp))
                        PlatformBar("Facebook", platformCounts["Facebook"] ?: 0, 15, Color(0xFF1877F2))
                        Spacer(modifier = Modifier.height(8.dp))
                        PlatformBar("Quora", platformCounts["Quora"] ?: 0, 15, Color(0xFFB92B27))
                    }
                }

                // Cities count card
                Card(
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                    shape = RoundedCornerShape(16.dp),
                    elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
                    modifier = Modifier.weight(1f)
                ) {
                    Column(
                        modifier = Modifier.padding(14.dp)
                    ) {
                        Text(
                            text = "Regional Cities",
                            fontWeight = FontWeight.Bold,
                            fontSize = 12.sp,
                            color = MaterialTheme.colorScheme.secondary
                        )
                        Spacer(modifier = Modifier.height(10.dp))

                        val cityCounts = viewModel.cityCounts
                        CityItem("Birmingham", cityCounts["Birmingham"] ?: 0)
                        CityItem("Leicester", cityCounts["Leicester"] ?: 0)
                        CityItem("Coventry", cityCounts["Coventry"] ?: 0)
                        CityItem("Nottingham", cityCounts["Nottingham"] ?: 0)
                    }
                }
            }
        }

        // --- 4. Key 2026 Insights & Upcoming Planned Activities (RAG report summary) ---
        item {
            Card(
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                shape = RoundedCornerShape(24.dp),
                border = androidx.compose.foundation.BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.3f)),
                elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(
                    modifier = Modifier.padding(16.dp)
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            Icon(
                                imageVector = Icons.Default.Event,
                                contentDescription = null,
                                tint = MaterialTheme.colorScheme.primary
                            )
                            Text(
                                text = "2026 Trend Intelligence",
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.Bold,
                                color = MaterialTheme.colorScheme.onSurface
                            )
                        }
                        
                        Badge(
                            containerColor = MaterialTheme.colorScheme.primary.copy(alpha = 0.1f),
                            contentColor = MaterialTheme.colorScheme.primary
                        ) {
                            Text(
                                text = "RAG-Sync: 2m ago",
                                fontSize = 9.sp,
                                fontWeight = FontWeight.Bold,
                                modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(14.dp))

                    InsightItem(
                        title = "Leicester Diwali Switch-On (October 2026)",
                        desc = "Major buzz around the introduction of a massive, eco-friendly drone light show instead of fireworks. However, the local diaspora is raising deep concerns about Belgrave Road traffic closures and is requesting the council to organize park-and-ride shuttle buses.",
                        emoji = "✨"
                    )

                    Spacer(modifier = Modifier.height(12.dp))

                    InsightItem(
                        title = "Coventry Navratri Garba (October 2026)",
                        desc = "Moving to a larger, premium venue to accommodate the surging diaspora. Tickets sold out in 10 minutes, triggering severe community complaints about ticket scalping and reselling on social media. Suggestion made to implement secure ID-linked ticketing.",
                        emoji = "🥁"
                    )
                }
            }
        }

        // --- 5. Retrospective 2026 Event Summary Insights ---
        item {
            Card(
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                shape = RoundedCornerShape(24.dp),
                border = androidx.compose.foundation.BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.3f)),
                elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(
                    modifier = Modifier.padding(16.dp)
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            Icon(
                                imageVector = Icons.Default.Forum,
                                contentDescription = null,
                                tint = MaterialTheme.colorScheme.secondary
                            )
                            Text(
                                text = "Retrospective 2026 Trends",
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.Bold,
                                color = MaterialTheme.colorScheme.onSurface
                            )
                        }

                        Badge(
                            containerColor = MaterialTheme.colorScheme.secondary.copy(alpha = 0.1f),
                            contentColor = MaterialTheme.colorScheme.secondary
                        ) {
                            Text(
                                text = "Consolidated",
                                fontSize = 9.sp,
                                fontWeight = FontWeight.Bold,
                                modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(14.dp))

                    InsightItem(
                        title = "Midlands Holi Festival (Birmingham)",
                        desc = "Praised for vibrant dhol players, colorful crowd and strong community engagement. Criticized heavily for expensive family tickets (£25/person) and extremely long, 1-hour lines for food stalls.",
                        emoji = "🎨"
                    )

                    Spacer(modifier = Modifier.height(12.dp))

                    InsightItem(
                        title = "Birmingham Vaisakhi Mela",
                        desc = "Very large attendance. Langar (free kitchen) praised with stellar reviews for organization. The core complaints relate to parking nightmares in Handsworth Park and lack of trash bins leading to littering.",
                        emoji = "🌾"
                    )

                    Spacer(modifier = Modifier.height(12.dp))

                    InsightItem(
                        title = "Midlands Indian Sports Day (Leicester)",
                        desc = "High nostalgia for traditional sports like Kabaddi and Kho-Kho. However, severe criticism regarding weather planning: summer rain caused a 3-hour delay due to a lack of an indoor backup plan.",
                        emoji = "🏆"
                    )
                }
            }
        }
    }
}

@Composable
fun SentimentLegendItem(label: String, percentage: Float, count: Int, color: Color) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Box(
            modifier = Modifier
                .size(10.dp)
                .clip(CircleShape)
                .background(color)
        )
        Spacer(modifier = Modifier.width(8.dp))
        Text(
            text = label,
            fontSize = 11.sp,
            fontWeight = FontWeight.Bold,
            modifier = Modifier.weight(1f)
        )
        Text(
            text = "$count (${percentage.roundToInt()}%)",
            fontSize = 11.sp,
            color = Color.Gray,
            fontWeight = FontWeight.Bold
        )
    }
}

@Composable
fun PlatformBar(platform: String, count: Int, total: Int, color: Color) {
    Column {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Text(platform, fontSize = 11.sp, fontWeight = FontWeight.Bold)
            Text("$count entries", fontSize = 11.sp, color = Color.Gray, fontWeight = FontWeight.Bold)
        }
        Spacer(modifier = Modifier.height(2.dp))
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(8.dp)
                .clip(CircleShape)
                .background(color.copy(alpha = 0.15f))
        ) {
            val fraction = if (total > 0) count.toFloat() / total.toFloat() else 0f
            Box(
                modifier = Modifier
                    .fillMaxWidth(fraction)
                    .fillMaxHeight()
                    .clip(CircleShape)
                    .background(color)
            )
        }
    }
}

@Composable
fun CityItem(city: String, count: Int) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 2.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Icon(
                imageVector = Icons.Default.LocationOn,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.secondary,
                modifier = Modifier.size(12.dp)
            )
            Spacer(modifier = Modifier.width(4.dp))
            Text(city, fontSize = 11.sp, fontWeight = FontWeight.Medium)
        }
        Text("$count", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.secondary)
    }
}

@Composable
fun EmojiIconBox(emoji: String) {
    val bgColor = when (emoji) {
        "🪔" -> Color(0xFFF0E68C).copy(alpha = 0.35f)
        "🥁" -> Color(0xFFEADDFF)
        "🎨" -> Color(0xFFFFF2AF).copy(alpha = 0.5f)
        "🌾" -> Color(0xFFD0E4FF)
        "🏆" -> Color(0xFFFFD700).copy(alpha = 0.2f)
        "✨" -> Color(0xFFF9F3B6)
        else -> MaterialTheme.colorScheme.surfaceVariant
    }
    Box(
        modifier = Modifier
            .size(40.dp)
            .clip(RoundedCornerShape(12.dp))
            .background(bgColor),
        contentAlignment = Alignment.Center
    ) {
        Text(text = emoji, fontSize = 20.sp)
    }
}

@Composable
fun InsightItem(title: String, desc: String, emoji: String) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(12.dp),
        verticalAlignment = Alignment.Top
    ) {
        EmojiIconBox(emoji = emoji)
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = title,
                fontSize = 12.sp,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onSurface
            )
            Spacer(modifier = Modifier.height(2.dp))
            Text(
                text = desc,
                fontSize = 11.sp,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                lineHeight = 15.sp
            )
        }
    }
}

@Composable
fun ChatTab(viewModel: DiasporaViewModel) {
    val messages by viewModel.chatMessages.collectAsState()
    val isLoading by viewModel.isChatLoading.collectAsState()
    val chatError by viewModel.chatError.collectAsState()

    var textInput by remember { androidx.compose.runtime.mutableStateOf("") }
    val focusManager = LocalFocusManager.current
    val listState = rememberLazyListState()

    // Scroll to bottom when a new message arrives
    LaunchedEffect(messages.size) {
        if (messages.isNotEmpty()) {
            listState.animateScrollToItem(messages.size - 1)
        }
    }

    val suggestedQuestions = listOf(
        "What are the main complaints about Holi 2026?",
        "What are upcoming Diwali activities in Leicester?",
        "Consolidate feedback on Coventry Garba.",
        "Which platform has the most negative posts?",
        "Who praised Vaisakhi Langar in Birmingham?"
    )

    Column(
        modifier = Modifier
            .fillMaxSize()
            .testTag("chat_tab_content")
    ) {
        // --- 1. Chat Area ---
        LazyColumn(
            state = listState,
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            items(messages) { message ->
                ChatBubble(message = message)
            }

            if (isLoading) {
                item {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(8.dp),
                        horizontalArrangement = Arrangement.Start,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Card(
                            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
                            shape = RoundedCornerShape(12.dp),
                            modifier = Modifier.widthIn(max = 280.dp)
                        ) {
                            Row(
                                modifier = Modifier.padding(12.dp),
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(8.dp)
                            ) {
                                CircularProgressIndicator(
                                    modifier = Modifier.size(16.dp),
                                    strokeWidth = 2.dp,
                                    color = MaterialTheme.colorScheme.primary
                                )
                                Text(
                                    text = "RAG Agent analyzing diaspora feed...",
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.Medium,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                            }
                        }
                    }
                }
            }

            if (chatError != null) {
                item {
                    Card(
                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer),
                        shape = RoundedCornerShape(8.dp),
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(top = 4.dp)
                    ) {
                        Text(
                            text = chatError ?: "",
                            color = MaterialTheme.colorScheme.onErrorContainer,
                            fontSize = 11.sp,
                            modifier = Modifier.padding(12.dp)
                        )
                    }
                }
            }
        }

        // --- 2. Suggested Questions Row ---
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .background(MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f))
                .padding(vertical = 10.dp)
        ) {
            Text(
                text = "⚡ QUICK ANALYTICS COMMANDS",
                fontSize = 9.sp,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.primary,
                modifier = Modifier.padding(start = 16.dp, end = 16.dp, bottom = 6.dp)
            )

            LazyColumn(
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(max = 110.dp),
                contentPadding = PaddingValues(horizontal = 16.dp),
                verticalArrangement = Arrangement.spacedBy(4.dp)
            ) {
                item {
                    @OptIn(ExperimentalLayoutApi::class)
                    FlowRow(
                        horizontalArrangement = Arrangement.spacedBy(6.dp),
                        verticalArrangement = Arrangement.spacedBy(6.dp),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        suggestedQuestions.forEach { question ->
                            Box(
                                modifier = Modifier
                                    .clip(RoundedCornerShape(8.dp))
                                    .background(MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.7f))
                                    .clickable {
                                        viewModel.sendChatMessage(question)
                                        focusManager.clearFocus()
                                    }
                                    .padding(horizontal = 10.dp, vertical = 6.dp)
                                    .testTag("quick_suggestion_chip_${question.replace(" ", "_")}")
                            ) {
                                Text(
                                    text = question,
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = MaterialTheme.colorScheme.onPrimaryContainer
                                )
                            }
                        }
                    }
                }
            }
        }

        // --- 3. Chat Input Bar ---
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .background(MaterialTheme.colorScheme.background)
                .padding(12.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            OutlinedTextField(
                value = textInput,
                onValueChange = { textInput = it },
                placeholder = { Text("Ask Diaspora RAG chatbot...", fontSize = 13.sp) },
                singleLine = true,
                shape = RoundedCornerShape(24.dp),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = MaterialTheme.colorScheme.primary,
                    unfocusedBorderColor = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.3f),
                    focusedContainerColor = MaterialTheme.colorScheme.surface,
                    unfocusedContainerColor = MaterialTheme.colorScheme.surface
                ),
                modifier = Modifier
                    .weight(1f)
                    .testTag("chat_input_field"),
                trailingIcon = {
                    if (textInput.isNotEmpty()) {
                        IconButton(onClick = { textInput = "" }) {
                            Icon(Icons.Default.Clear, contentDescription = "Clear text", modifier = Modifier.size(16.dp))
                        }
                    }
                }
            )

            Button(
                onClick = {
                    if (textInput.trim().isNotEmpty()) {
                        viewModel.sendChatMessage(textInput)
                        textInput = ""
                        focusManager.clearFocus()
                    }
                },
                enabled = textInput.trim().isNotEmpty() && !isLoading,
                shape = CircleShape,
                colors = ButtonDefaults.buttonColors(
                    containerColor = MaterialTheme.colorScheme.primary,
                    contentColor = MaterialTheme.colorScheme.onPrimary
                ),
                contentPadding = PaddingValues(12.dp),
                modifier = Modifier
                    .size(48.dp)
                    .testTag("submit_chat_button")
            ) {
                Icon(
                    imageVector = Icons.AutoMirrored.Filled.Send,
                    contentDescription = "Send",
                    modifier = Modifier.size(20.dp)
                )
            }
        }
    }
}

@Composable
fun ChatBubble(message: ChatMessage) {
    val isUser = message.sender == MessageSender.USER
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = if (isUser) Arrangement.End else Arrangement.Start
    ) {
        Row(
            modifier = Modifier.widthIn(max = 300.dp),
            horizontalArrangement = if (isUser) Arrangement.End else Arrangement.Start
        ) {
            Card(
                colors = CardDefaults.cardColors(
                    containerColor = if (isUser) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.surfaceVariant
                ),
                shape = RoundedCornerShape(
                    topStart = 16.dp,
                    topEnd = 16.dp,
                    bottomStart = if (isUser) 16.dp else 4.dp,
                    bottomEnd = if (isUser) 4.dp else 16.dp
                ),
                elevation = CardDefaults.cardElevation(defaultElevation = 1.dp)
            ) {
                Column(
                    modifier = Modifier.padding(12.dp)
                ) {
                    Text(
                        text = if (isUser) "YOU" else "DIASPORA BOT (RAG)",
                        fontSize = 9.sp,
                        fontWeight = FontWeight.ExtraBold,
                        color = if (isUser) MaterialTheme.colorScheme.onPrimary.copy(alpha = 0.7f) else MaterialTheme.colorScheme.primary,
                        modifier = Modifier.padding(bottom = 2.dp)
                    )

                    Text(
                        text = message.text,
                        fontSize = 12.sp,
                        color = if (isUser) MaterialTheme.colorScheme.onPrimary else MaterialTheme.colorScheme.onSurfaceVariant,
                        lineHeight = 16.sp,
                        modifier = Modifier.testTag("chat_message_text")
                    )
                }
            }
        }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun ExplorerTab(viewModel: DiasporaViewModel) {
    val items by viewModel.filteredItems.collectAsState()
    val searchQuery by viewModel.searchQuery.collectAsState()
    val selectedPlatform by viewModel.selectedPlatform.collectAsState()
    val selectedSentiment by viewModel.selectedSentiment.collectAsState()
    val selectedCity by viewModel.selectedCity.collectAsState()

    val focusManager = LocalFocusManager.current

    Column(
        modifier = Modifier
            .fillMaxSize()
            .testTag("explorer_tab_content")
    ) {
        // --- 1. Search Bar ---
        OutlinedTextField(
            value = searchQuery,
            onValueChange = { viewModel.updateSearchQuery(it) },
            leadingIcon = { Icon(Icons.Default.Search, contentDescription = "Search icon") },
            trailingIcon = {
                if (searchQuery.isNotEmpty()) {
                    IconButton(onClick = { viewModel.updateSearchQuery("") }) {
                        Icon(Icons.Default.Clear, contentDescription = "Clear search")
                    }
                }
            },
            placeholder = { Text("Search by event, comment text, user...", fontSize = 13.sp) },
            singleLine = true,
            colors = OutlinedTextFieldDefaults.colors(
                focusedBorderColor = MaterialTheme.colorScheme.primary,
                focusedContainerColor = MaterialTheme.colorScheme.surface,
                unfocusedContainerColor = MaterialTheme.colorScheme.surface
            ),
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 12.dp)
                .testTag("search_input_field")
        )

        // --- 2. Advanced Interactive Filter Row ---
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(start = 16.dp, end = 16.dp, bottom = 12.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            // Platform Filters
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                Text("Platform:", fontSize = 10.sp, fontWeight = FontWeight.Bold, color = Color.Gray, modifier = Modifier.width(55.dp))
                listOf(null, "Twitter", "Facebook", "Quora").forEach { platform ->
                    val isSelected = selectedPlatform == platform
                    Box(
                        modifier = Modifier
                            .clip(RoundedCornerShape(8.dp))
                            .background(
                                if (isSelected) MaterialTheme.colorScheme.primary
                                else MaterialTheme.colorScheme.surfaceVariant
                            )
                            .clickable { viewModel.selectPlatform(platform) }
                            .padding(horizontal = 10.dp, vertical = 4.dp)
                    ) {
                        Text(
                            text = platform ?: "All",
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            color = if (isSelected) MaterialTheme.colorScheme.onPrimary else MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }

            // Sentiment Filters
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                Text("Sentiment:", fontSize = 10.sp, fontWeight = FontWeight.Bold, color = Color.Gray, modifier = Modifier.width(55.dp))
                listOf(null, "Positive", "Neutral", "Negative").forEach { sentiment ->
                    val isSelected = selectedSentiment == sentiment
                    Box(
                        modifier = Modifier
                            .clip(RoundedCornerShape(8.dp))
                            .background(
                                if (isSelected) {
                                    when (sentiment) {
                                        "Positive" -> Color(0xFF2E7D32)
                                        "Neutral" -> Color(0xFFF9A825)
                                        "Negative" -> Color(0xFFC62828)
                                        else -> MaterialTheme.colorScheme.primary
                                    }
                                } else {
                                    MaterialTheme.colorScheme.surfaceVariant
                                }
                            )
                            .clickable { viewModel.selectSentiment(sentiment) }
                            .padding(horizontal = 10.dp, vertical = 4.dp)
                    ) {
                        Text(
                            text = sentiment ?: "All",
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            color = if (isSelected) Color.White else MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }

            // City Filters
            FlowRow(
                horizontalArrangement = Arrangement.spacedBy(6.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("City:", fontSize = 10.sp, fontWeight = FontWeight.Bold, color = Color.Gray, modifier = Modifier.width(55.dp))
                listOf(null, "Birmingham", "Leicester", "Coventry", "Nottingham").forEach { city ->
                    val isSelected = selectedCity == city
                    Box(
                        modifier = Modifier
                            .padding(vertical = 2.dp)
                            .clip(RoundedCornerShape(8.dp))
                            .background(
                                if (isSelected) MaterialTheme.colorScheme.secondary
                                else MaterialTheme.colorScheme.surfaceVariant
                            )
                            .clickable { viewModel.selectCity(city) }
                            .padding(horizontal = 10.dp, vertical = 4.dp)
                    ) {
                        Text(
                            text = city ?: "All",
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            color = if (isSelected) MaterialTheme.colorScheme.onSecondary else MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }
        }

        // --- 3. Results Header ---
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(start = 16.dp, end = 16.dp, bottom = 4.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "${items.size} Feed items matched",
                fontSize = 12.sp,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.primary
            )

            if (selectedPlatform != null || selectedSentiment != null || selectedCity != null || searchQuery.isNotEmpty()) {
                Text(
                    text = "Clear filters",
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.secondary,
                    modifier = Modifier
                        .clickable { viewModel.clearFilters() }
                        .padding(4.dp)
                )
            }
        }

        // --- 4. Cards Feed ---
        if (items.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .weight(1f),
                contentAlignment = Alignment.Center
            ) {
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.spacedBy(8.dp),
                    modifier = Modifier.padding(32.dp)
                ) {
                    Icon(
                        imageVector = Icons.Default.Info,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.primary.copy(alpha = 0.5f),
                        modifier = Modifier.size(48.dp)
                    )
                    Text(
                        text = "No diaspora feed items match your criteria.",
                        fontWeight = FontWeight.Bold,
                        fontSize = 14.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Text(
                        text = "Try clearing filters or search query to see full consolidated 2026 data.",
                        fontSize = 12.sp,
                        color = Color.Gray,
                        modifier = Modifier.clickable { viewModel.clearFilters() }
                    )
                }
            }
        } else {
            LazyColumn(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f),
                contentPadding = PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                items(items, key = { it.id }) { item ->
                    FeedbackCard(item = item)
                }
            }
        }
    }
}

@Composable
fun FeedbackCard(item: FeedbackItem) {
    Card(
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        shape = RoundedCornerShape(16.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
        modifier = Modifier
            .fillMaxWidth()
            .clickable { }
            .testTag("feedback_card_${item.id}")
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            // Top Row: Author & Platform Badge, Date
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    // Custom platform icon representation
                    val platformColor = when (item.platform) {
                        "Twitter" -> Color(0xFF1DA1F2)
                        "Facebook" -> Color(0xFF1877F2)
                        "Quora" -> Color(0xFFB92B27)
                        else -> MaterialTheme.colorScheme.primary
                    }

                    Box(
                        modifier = Modifier
                            .size(18.dp)
                            .clip(CircleShape)
                            .background(platformColor),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = item.platform.first().toString(),
                            color = Color.White,
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }

                    Text(
                        text = item.author,
                        fontWeight = FontWeight.Bold,
                        fontSize = 13.sp,
                        color = MaterialTheme.colorScheme.onSurface
                    )
                }

                Text(
                    text = item.date,
                    fontSize = 11.sp,
                    color = Color.Gray
                )
            }

            Spacer(modifier = Modifier.height(8.dp))

            // Event Title
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                Icon(
                    imageVector = Icons.Default.Event,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.primary,
                    modifier = Modifier.size(14.dp)
                )
                Text(
                    text = item.event,
                    fontWeight = FontWeight.Bold,
                    fontSize = 13.sp,
                    color = MaterialTheme.colorScheme.primary,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )

                if (item.isUpcoming) {
                    Badge(
                        containerColor = MaterialTheme.colorScheme.tertiary.copy(alpha = 0.15f),
                        contentColor = MaterialTheme.colorScheme.tertiary
                    ) {
                        Text(
                            text = "PLANNED",
                            fontSize = 8.sp,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.padding(horizontal = 4.dp)
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            // Message text
            Text(
                text = item.text,
                fontSize = 12.sp,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                lineHeight = 17.sp
            )

            Spacer(modifier = Modifier.height(12.dp))

            // Bottom row: Tags and badges
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                // City Location Tag
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(4.dp)
                ) {
                    Icon(
                        imageVector = Icons.Default.LocationOn,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.secondary,
                        modifier = Modifier.size(14.dp)
                    )
                    Text(
                        text = item.city,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Medium,
                        color = MaterialTheme.colorScheme.secondary
                    )
                }

                // Sentiment Badge
                val (badgeBg, badgeFg) = when (item.sentiment) {
                    "Positive" -> Color(0xFFE8F5E9) to Color(0xFF2E7D32)
                    "Neutral" -> Color(0xFFFFFDE7) to Color(0xFFF57F17)
                    "Negative" -> Color(0xFFFFEBEE) to Color(0xFFC62828)
                    else -> MaterialTheme.colorScheme.primaryContainer to MaterialTheme.colorScheme.onPrimaryContainer
                }

                Badge(
                    containerColor = badgeBg,
                    contentColor = badgeFg
                ) {
                    Text(
                        text = item.sentiment.uppercase(),
                        fontWeight = FontWeight.Bold,
                        fontSize = 9.sp,
                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                    )
                }
            }
        }
    }
}
