"""
📊 Count Pulse Bot - Professional Word Counter
Real-time text analysis with writing pace tracking and detailed statistics
"""

import os
import re
import io
import math
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from collections import Counter
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# ==================== CONFIGURATION ====================

# Try multiple possible token variable names
BOT_TOKEN = (
    os.environ.get("TELEGRAM_TOKEN") or
    os.environ.get("TELEGRAM_BOT_TOKEN") or
    os.environ.get("BOT_TOKEN")
)

# If token is not set, try reading from .env file
if not BOT_TOKEN:
    try:
        from dotenv import load_dotenv
        load_dotenv()
        BOT_TOKEN = (
            os.environ.get("TELEGRAM_TOKEN") or
            os.environ.get("TELEGRAM_BOT_TOKEN") or
            os.environ.get("BOT_TOKEN")
        )
    except:
        pass

# If still no token, show error
if not BOT_TOKEN:
    print("=" * 60)
    print("❌ ERROR: No Telegram Bot Token found!")
    print("=" * 60)
    print("Please set one of these environment variables:")
    print("  - TELEGRAM_TOKEN")
    print("  - TELEGRAM_BOT_TOKEN")
    print("  - BOT_TOKEN")
    print("=" * 60)
    raise ValueError("❌ No Telegram Bot Token found in environment variables!")

BOT_NAME = "Count Pulse Bot"
BOT_USERNAME = "count_pulse_bot"
BOT_VERSION = "1.0.0"

# ==================== USER DATA ====================

user_data: Dict[int, Dict] = {}

def get_user_data(user_id: int) -> Dict:
    if user_id not in user_data:
        user_data[user_id] = {
            "history": [],
            "total_words": 0,
            "total_chars": 0,
            "total_analyses": 0
        }
    return user_data[user_id]

# ==================== KEYBOARDS ====================

def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("📊 Analyze Text", callback_data="analyze")],
        [InlineKeyboardButton("📈 My Stats", callback_data="stats")],
        [InlineKeyboardButton("📝 Word Frequency", callback_data="frequency")],
        [InlineKeyboardButton("📋 Readability Score", callback_data="readability")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_analysis_options_keyboard():
    keyboard = [
        [InlineKeyboardButton("📊 Full Analysis", callback_data="full_analysis")],
        [InlineKeyboardButton("📝 Word Frequency", callback_data="freq_analysis")],
        [InlineKeyboardButton("📈 Readability", callback_data="read_analysis")],
        [InlineKeyboardButton("📋 Export Report", callback_data="export_report")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==================== TEXT ANALYSIS FUNCTIONS ====================

def analyze_text(text: str) -> Dict:
    """
    Comprehensive text analysis
    Returns: Dict with all statistics
    """
    # Clean text
    clean_text = text.strip()
    if not clean_text:
        return {"error": "Empty text"}
    
    # Basic counts
    word_count = len(clean_text.split())
    char_count = len(clean_text)
    char_count_no_spaces = len(clean_text.replace(" ", ""))
    
    # Sentence count (split by . ! ?)
    sentences = re.split(r'[.!?]+', clean_text)
    sentence_count = len([s for s in sentences if s.strip()])
    
    # Paragraph count (split by double newline)
    paragraphs = [p for p in clean_text.split('\n\n') if p.strip()]
    paragraph_count = len(paragraphs)
    
    # Syllable count (approximate)
    syllable_count = count_syllables(clean_text)
    
    # Reading time
    reading_time_min = word_count / 200  # Average reading speed: 200 words/min
    reading_time_sec = reading_time_min * 60
    
    # Speaking time (average: 150 words/min)
    speaking_time_min = word_count / 150
    
    # Average word length
    words = clean_text.split()
    avg_word_length = sum(len(w) for w in words) / word_count if word_count > 0 else 0
    
    # Average sentence length
    avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
    
    # Longest word
    longest_word = max(words, key=len) if words else ""
    longest_word_length = len(longest_word)
    
    # Shortest word
    shortest_word = min(words, key=len) if words else ""
    shortest_word_length = len(shortest_word)
    
    # Unique words
    unique_words = set(w.lower() for w in words)
    unique_word_count = len(unique_words)
    
    # Lexical diversity (Type-Token Ratio)
    ttr = unique_word_count / word_count if word_count > 0 else 0
    
    # Word frequency
    word_freq = Counter(w.lower() for w in words)
    top_words = word_freq.most_common(10)
    
    # Character frequency
    char_freq = Counter(c.lower() for c in clean_text if c.isalpha())
    top_chars = char_freq.most_common(10)
    
    # Readability scores
    flesch_score = calculate_flesch_reading_ease(clean_text)
    flesch_grade = calculate_flesch_kincaid_grade(clean_text)
    
    # Complexity
    complex_words = count_complex_words(words)
    complex_word_percentage = (complex_words / word_count * 100) if word_count > 0 else 0
    
    # Density
    density = calculate_keyword_density(text)
    
    return {
        "word_count": word_count,
        "char_count": char_count,
        "char_count_no_spaces": char_count_no_spaces,
        "sentence_count": sentence_count,
        "paragraph_count": paragraph_count,
        "syllable_count": syllable_count,
        "reading_time_min": reading_time_min,
        "reading_time_sec": reading_time_sec,
        "speaking_time_min": speaking_time_min,
        "avg_word_length": avg_word_length,
        "avg_sentence_length": avg_sentence_length,
        "longest_word": longest_word,
        "longest_word_length": longest_word_length,
        "shortest_word": shortest_word,
        "shortest_word_length": shortest_word_length,
        "unique_word_count": unique_word_count,
        "ttr": ttr,
        "top_words": top_words,
        "top_chars": top_chars,
        "flesch_score": flesch_score,
        "flesch_grade": flesch_grade,
        "complex_words": complex_words,
        "complex_word_percentage": complex_word_percentage,
        "density": density,
    }

def count_syllables(text: str) -> int:
    """Count syllables in text (approximate)"""
    text = text.lower()
    syllables = 0
    vowels = "aeiouy"
    
    # Remove punctuation
    text = re.sub(r'[^a-z\s]', '', text)
    
    for word in text.split():
        word_syllables = 0
        prev_char = ""
        for char in word:
            if char in vowels and prev_char not in vowels:
                word_syllables += 1
            prev_char = char
        
        # Handle silent e
        if word.endswith('e'):
            word_syllables -= 1
        
        # Minimum 1 syllable per word
        if word_syllables == 0:
            word_syllables = 1
        
        syllables += word_syllables
    
    return syllables

def calculate_flesch_reading_ease(text: str) -> float:
    """Calculate Flesch Reading Ease score"""
    words = text.split()
    sentences = re.split(r'[.!?]+', text)
    sentences = [s for s in sentences if s.strip()]
    
    if not words or not sentences:
        return 0
    
    word_count = len(words)
    sentence_count = len(sentences)
    syllable_count = count_syllables(text)
    
    # Flesch Reading Ease formula
    score = 206.835 - 1.015 * (word_count / sentence_count) - 84.6 * (syllable_count / word_count)
    return max(0, min(100, score))

def calculate_flesch_kincaid_grade(text: str) -> float:
    """Calculate Flesch-Kincaid Grade Level"""
    words = text.split()
    sentences = re.split(r'[.!?]+', text)
    sentences = [s for s in sentences if s.strip()]
    
    if not words or not sentences:
        return 0
    
    word_count = len(words)
    sentence_count = len(sentences)
    syllable_count = count_syllables(text)
    
    # Flesch-Kincaid Grade Level formula
    grade = 0.39 * (word_count / sentence_count) + 11.8 * (syllable_count / word_count) - 15.59
    return max(0, grade)

def count_complex_words(words: List[str]) -> int:
    """Count complex words (3+ syllables)"""
    complex_words = 0
    for word in words:
        syllables = count_syllables(word)
        if syllables >= 3:
            complex_words += 1
    return complex_words

def calculate_keyword_density(text: str) -> Dict[str, float]:
    """Calculate keyword density for important words"""
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    word_count = len(words)
    
    if word_count == 0:
        return {}
    
    # Exclude common stop words
    stop_words = {'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i',
                  'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
                  'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her',
                  'she', 'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there',
                  'their', 'what', 'so', 'up', 'out', 'if', 'about', 'who', 'get',
                  'which', 'go', 'me', 'when', 'make', 'can', 'like', 'time', 'no',
                  'just', 'him', 'know', 'take', 'people', 'into', 'year', 'your',
                  'good', 'some', 'could', 'them', 'see', 'other', 'than', 'then',
                  'now', 'look', 'only', 'come', 'its', 'over', 'think', 'also',
                  'back', 'after', 'use', 'two', 'how', 'our', 'work', 'first',
                  'well', 'way', 'even', 'new', 'want', 'because', 'any', 'these',
                  'give', 'day', 'most', 'us'}
    
    density = {}
    for word, count in Counter(words).items():
        if word not in stop_words and len(word) > 2:
            density[word] = (count / word_count) * 100
    
    # Return top 10
    return dict(sorted(density.items(), key=lambda x: x[1], reverse=True)[:10])

def format_analysis_result(result: Dict) -> str:
    """Format analysis result for display"""
    if "error" in result:
        return "❌ " + result["error"]
    
    text = (
        f"📊 **Text Analysis Results**\n\n"
        f"📝 **Words:** {result['word_count']:,}\n"
        f"🔤 **Characters:** {result['char_count']:,}\n"
        f"🔢 **Characters (no spaces):** {result['char_count_no_spaces']:,}\n"
        f"📖 **Sentences:** {result['sentence_count']:,}\n"
        f"📄 **Paragraphs:** {result['paragraph_count']:,}\n"
        f"🔊 **Syllables:** {result['syllable_count']:,}\n\n"
        f"⏱️ **Reading Time:** {result['reading_time_min']:.1f} min ({result['reading_time_sec']:.0f} sec)\n"
        f"🗣️ **Speaking Time:** {result['speaking_time_min']:.1f} min\n\n"
        f"📏 **Avg Word Length:** {result['avg_word_length']:.2f} characters\n"
        f"📐 **Avg Sentence Length:** {result['avg_sentence_length']:.2f} words\n"
        f"🏆 **Longest Word:** {result['longest_word']} ({result['longest_word_length']} chars)\n"
        f"📏 **Shortest Word:** {result['shortest_word']} ({result['shortest_word_length']} chars)\n\n"
        f"🔄 **Unique Words:** {result['unique_word_count']:,}\n"
        f"📊 **Lexical Diversity (TTR):** {result['ttr']:.2%}\n"
        f"🧩 **Complex Words:** {result['complex_words']:,} ({result['complex_word_percentage']:.1f}%)\n\n"
        f"📖 **Flesch Reading Ease:** {result['flesch_score']:.1f} ({get_readability_level(result['flesch_score'])})\n"
        f"📚 **Flesch-Kincaid Grade:** {result['flesch_grade']:.1f}\n"
    )
    return text

def get_readability_level(score: float) -> str:
    """Get readability level from Flesch score"""
    if score >= 90:
        return "Very Easy (5th grade)"
    elif score >= 80:
        return "Easy (6th grade)"
    elif score >= 70:
        return "Fairly Easy (7th grade)"
    elif score >= 60:
        return "Plain English (8th-9th grade)"
    elif score >= 50:
        return "Fairly Difficult (10th-12th grade)"
    elif score >= 30:
        return "Difficult (College level)"
    else:
        return "Very Difficult (College graduate)"

def create_export_report(text: str, result: Dict) -> bytes:
    """Create a text report for export"""
    report = f"""
📊 COUNT PULSE BOT - TEXT ANALYSIS REPORT
═══════════════════════════════════════
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📝 INPUT TEXT:
───────────────────────────────────────
{text[:500]}{'...' if len(text) > 500 else ''}

📊 STATISTICS:
───────────────────────────────────────
Words:              {result['word_count']:,}
Characters:         {result['char_count']:,}
Characters (no spaces): {result['char_count_no_spaces']:,}
Sentences:          {result['sentence_count']:,}
Paragraphs:         {result['paragraph_count']:,}
Syllables:          {result['syllable_count']:,}

⏱️ TIME ANALYSIS:
───────────────────────────────────────
Reading Time:       {result['reading_time_min']:.1f} min ({result['reading_time_sec']:.0f} sec)
Speaking Time:      {result['speaking_time_min']:.1f} min

📏 LENGTH ANALYSIS:
───────────────────────────────────────
Avg Word Length:    {result['avg_word_length']:.2f} chars
Avg Sentence Length: {result['avg_sentence_length']:.2f} words
Longest Word:       {result['longest_word']} ({result['longest_word_length']} chars)
Shortest Word:      {result['shortest_word']} ({result['shortest_word_length']} chars)

🔄 VOCABULARY:
───────────────────────────────────────
Unique Words:       {result['unique_word_count']:,}
Lexical Diversity:  {result['ttr']:.2%}
Complex Words:      {result['complex_words']:,} ({result['complex_word_percentage']:.1f}%)

📖 READABILITY:
───────────────────────────────────────
Flesch Reading Ease: {result['flesch_score']:.1f} ({get_readability_level(result['flesch_score'])})
Flesch-Kincaid Grade: {result['flesch_grade']:.1f}

📝 TOP 10 WORDS:
───────────────────────────────────────
"""
    for word, count in result['top_words'][:10]:
        report += f"{word}: {count}\n"
    
    report += """
📈 KEYWORD DENSITY:
───────────────────────────────────────
"""
    for word, density in result['density'].items():
        report += f"{word}: {density:.1f}%\n"
    
    return report.encode('utf-8')

def create_word_frequency_image(top_words: List[Tuple[str, int]]) -> bytes:
    """Create a visual word frequency chart"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        width = 500
        height = 50 + len(top_words) * 30
        img = Image.new('RGB', (width, height), color='#FFFFFF')
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        except:
            font = ImageFont.load_default()
        
        max_count = top_words[0][1] if top_words else 1
        
        y = 10
        for word, count in top_words[:15]:
            # Draw word
            draw.text((10, y), f"{word}", fill=(0, 0, 0), font=font)
            
            # Draw bar
            bar_width = int((count / max_count) * 300)
            draw.rectangle([120, y, 120 + bar_width, y + 20], fill=(100, 150, 255))
            
            # Draw count
            draw.text((430, y), str(count), fill=(0, 0, 0), font=font)
            y += 30
        
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes.getvalue()
        
    except Exception as e:
        print(f"Chart error: {e}")
        return None

# ==================== COMMAND HANDLERS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    data = get_user_data(user_id)
    
    welcome = (
        f"📊 **Welcome to {BOT_NAME}!**\n\n"
        f"👋 Hello @{user.username or user.first_name}!\n\n"
        f"Your professional text analysis assistant.\n\n"
        f"✨ **Features:**\n"
        f"• 📊 Real-time text analysis\n"
        f"• 📈 Writing pace tracking\n"
        f"• 📝 Word frequency analysis\n"
        f"• 📋 Readability scores\n"
        f"• 💾 Export reports\n"
        f"• 📊 Usage statistics\n\n"
        f"📊 **Your Stats:**\n"
        f"• Total words analyzed: {data['total_words']:,}\n"
        f"• Total characters: {data['total_chars']:,}\n"
        f"• Total analyses: {data['total_analyses']}\n\n"
        f"⬇️ Send me any text or use the buttons below!"
    )
    
    await update.message.reply_text(
        welcome,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        f"📖 **{BOT_NAME} User Guide**\n\n"
        "**📊 Analyze Text**\n"
        "• Send any text message\n"
        "• Click 'Analyze Text' button\n"
        "• Get detailed statistics\n\n"
        "**📈 Features Available:**\n"
        "• Word & Character Count\n"
        "• Reading & Speaking Time\n"
        "• Sentence & Paragraph Count\n"
        "• Syllable Count\n"
        "• Vocabulary Analysis\n"
        "• Readability Scores\n"
        "• Word Frequency\n"
        "• Keyword Density\n\n"
        "**📋 Commands:**\n"
        "/start - Main menu\n"
        "/help - This help\n"
        "/stats - Your statistics\n"
        "/analyze - Analyze text"
    )
    
    await update.message.reply_text(
        help_text,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = get_user_data(user_id)
    
    stats_text = (
        f"📊 **Your Statistics**\n\n"
        f"📝 Total analyses: {data['total_analyses']}\n"
        f"📖 Total words analyzed: {data['total_words']:,}\n"
        f"🔤 Total characters analyzed: {data['total_chars']:,}\n\n"
        f"📅 Account active since: {datetime.now().strftime('%Y-%m-%d')}"
    )
    
    await update.message.reply_text(
        stats_text,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

# ==================== CALLBACK HANDLERS ====================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = str(update.effective_user.id)
    data = get_user_data(user_id)
    
    action = query.data
    
    if action == "analyze":
        await query.edit_message_text(
            "📊 **Send me any text to analyze!**\n\n"
            "I'll provide:\n"
            "• Word & Character count\n"
            "• Reading time\n"
            "• Sentence analysis\n"
            "• Vocabulary stats\n"
            "• Readability scores\n\n"
            "Just send any text message!",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        context.user_data["action"] = "analyze_waiting"
        
    elif action == "stats":
        stats_text = (
            f"📊 **Your Statistics**\n\n"
            f"📝 Total analyses: {data['total_analyses']}\n"
            f"📖 Total words analyzed: {data['total_words']:,}\n"
            f"🔤 Total characters analyzed: {data['total_chars']:,}\n\n"
            f"📅 Account active since: {datetime.now().strftime('%Y-%m-%d')}"
        )
        await query.edit_message_text(
            stats_text,
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        
    elif action == "frequency":
        await query.edit_message_text(
            "📝 **Word Frequency Analysis**\n\n"
            "Send me text to analyze word frequency!\n\n"
            "I'll show:\n"
            "• Most common words\n"
            "• Word counts\n"
            "• Percentage breakdown",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        context.user_data["action"] = "freq_waiting"
        
    elif action == "readability":
        await query.edit_message_text(
            "📋 **Readability Score**\n\n"
            "Send me text to analyze readability!\n\n"
            "I'll calculate:\n"
            "• Flesch Reading Ease\n"
            "• Flesch-Kincaid Grade\n"
            "• Reading level\n"
            "• Text complexity",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        context.user_data["action"] = "read_waiting"
        
    elif action == "help":
        await help_command(update, context)
        
    elif action == "back":
        await query.edit_message_text(
            "🏠 **Main Menu**\n\n"
            "What would you like to analyze?",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        context.user_data["action"] = None
        
    elif action == "full_analysis":
        if "last_text" not in context.user_data:
            await query.edit_message_text(
                "❌ No text to analyze. Send me some text first!",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
            return
        
        text = context.user_data["last_text"]
        result = analyze_text(text)
        
        if result and "error" not in result:
            formatted = format_analysis_result(result)
            await query.message.reply_text(
                formatted,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📊 Full Analysis", callback_data="full_analysis")],
                    [InlineKeyboardButton("📝 Word Frequency", callback_data="freq_analysis")],
                    [InlineKeyboardButton("📈 Readability", callback_data="read_analysis")],
                    [InlineKeyboardButton("📋 Export Report", callback_data="export_report")],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="back")]
                ])
            )
            
            # Update user stats
            data["total_words"] += result["word_count"]
            data["total_chars"] += result["char_count"]
            data["total_analyses"] += 1
            
    elif action == "freq_analysis":
        if "last_text" not in context.user_data:
            await query.edit_message_text(
                "❌ No text to analyze. Send me some text first!",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
            return
        
        text = context.user_data["last_text"]
        result = analyze_text(text)
        
        if result and "error" not in result:
            freq_text = "📝 **Top 15 Most Common Words**\n\n"
            for word, count in result["top_words"][:15]:
                percentage = (count / result["word_count"]) * 100
                freq_text += f"• **{word}**: {count} times ({percentage:.1f}%)\n"
            
            # Create frequency chart
            chart_data = create_word_frequency_image(result["top_words"][:15])
            
            if chart_data:
                await query.message.reply_photo(
                    photo=io.BytesIO(chart_data),
                    caption=freq_text,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📊 Full Analysis", callback_data="full_analysis")],
                        [InlineKeyboardButton("🏠 Main Menu", callback_data="back")]
                    ])
                )
            else:
                await query.message.reply_text(
                    freq_text,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📊 Full Analysis", callback_data="full_analysis")],
                        [InlineKeyboardButton("🏠 Main Menu", callback_data="back")]
                    ])
                )
            
    elif action == "read_analysis":
        if "last_text" not in context.user_data:
            await query.edit_message_text(
                "❌ No text to analyze. Send me some text first!",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
            return
        
        text = context.user_data["last_text"]
        result = analyze_text(text)
        
        if result and "error" not in result:
            read_text = (
                f"📈 **Readability Analysis**\n\n"
                f"📖 **Flesch Reading Ease:** {result['flesch_score']:.1f}\n"
                f"📚 **Level:** {get_readability_level(result['flesch_score'])}\n\n"
                f"🎓 **Flesch-Kincaid Grade:** {result['flesch_grade']:.1f}\n\n"
                f"🧩 **Complex Words:** {result['complex_words']:,} ({result['complex_word_percentage']:.1f}%)\n"
                f"🔄 **Lexical Diversity:** {result['ttr']:.2%}\n\n"
                f"📏 **Avg Word Length:** {result['avg_word_length']:.2f} chars\n"
                f"📐 **Avg Sentence Length:** {result['avg_sentence_length']:.2f} words\n\n"
                f"💡 **Interpretation:**\n"
                f"• **{get_readability_level(result['flesch_score'])}**\n"
                f"• Recommended for **Grade {int(result['flesch_grade'])}** level"
            )
            await query.message.reply_text(
                read_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📊 Full Analysis", callback_data="full_analysis")],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="back")]
                ])
            )
            
    elif action == "export_report":
        if "last_text" not in context.user_data:
            await query.edit_message_text(
                "❌ No text to export. Send me some text first!",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
            return
        
        text = context.user_data["last_text"]
        result = analyze_text(text)
        
        if result and "error" not in result:
            report = create_export_report(text, result)
            await query.message.reply_document(
                document=io.BytesIO(report),
                filename=f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                caption="📋 **Analysis Report Exported!**\n\nFull text analysis report attached.",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )

# ==================== MESSAGE HANDLERS ====================

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages for analysis"""
    user_id = str(update.effective_user.id)
    data = get_user_data(user_id)
    text = update.message.text.strip()
    
    if not text:
        await update.message.reply_text(
            "❌ Please send some text to analyze!",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Check for commands
    action = context.user_data.get("action", "")
    
    # Analyze the text
    result = analyze_text(text)
    
    if "error" in result:
        await update.message.reply_text(
            "❌ Could not analyze the text. Please try again.",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Store for later use
    context.user_data["last_text"] = text
    
    # Update user stats
    data["total_words"] += result["word_count"]
    data["total_chars"] += result["char_count"]
    data["total_analyses"] += 1
    
    # Format response based on action
    if action == "freq_waiting":
        freq_text = "📝 **Top 15 Most Common Words**\n\n"
        for word, count in result["top_words"][:15]:
            percentage = (count / result["word_count"]) * 100
            freq_text += f"• **{word}**: {count} times ({percentage:.1f}%)\n"
        
        chart_data = create_word_frequency_image(result["top_words"][:15])
        
        if chart_data:
            await update.message.reply_photo(
                photo=io.BytesIO(chart_data),
                caption=freq_text,
                parse_mode="Markdown",
                reply_markup=get_analysis_options_keyboard()
            )
        else:
            await update.message.reply_text(
                freq_text,
                parse_mode="Markdown",
                reply_markup=get_analysis_options_keyboard()
            )
        context.user_data["action"] = None
        
    elif action == "read_waiting":
        read_text = (
            f"📈 **Readability Analysis**\n\n"
            f"📖 **Flesch Reading Ease:** {result['flesch_score']:.1f}\n"
            f"📚 **Level:** {get_readability_level(result['flesch_score'])}\n\n"
            f"🎓 **Flesch-Kincaid Grade:** {result['flesch_grade']:.1f}\n\n"
            f"🧩 **Complex Words:** {result['complex_words']:,} ({result['complex_word_percentage']:.1f}%)\n"
            f"🔄 **Lexical Diversity:** {result['ttr']:.2%}\n\n"
            f"💡 **Interpretation:**\n"
            f"• **{get_readability_level(result['flesch_score'])}**\n"
            f"• Recommended for **Grade {int(result['flesch_grade'])}** level"
        )
        await update.message.reply_text(
            read_text,
            parse_mode="Markdown",
            reply_markup=get_analysis_options_keyboard()
        )
        context.user_data["action"] = None
        
    else:
        # Full analysis
        formatted = format_analysis_result(result)
        await update.message.reply_text(
            formatted,
            parse_mode="Markdown",
            reply_markup=get_analysis_options_keyboard()
        )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle document files for analysis"""
    try:
        document = update.message.document
        
        # Check if it's a text file
        if not document.mime_type or not document.mime_type.startswith('text/'):
            await update.message.reply_text(
                "❌ Please send a text file (.txt, .docx, etc.)",
                reply_markup=get_main_keyboard()
            )
            return
        
        # Download file
        file = await document.get_file()
        file_content = await file.download_as_bytearray()
        
        try:
            text = file_content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                text = file_content.decode('latin-1')
            except:
                await update.message.reply_text(
                    "❌ Could not read the file. Please send a plain text file.",
                    reply_markup=get_main_keyboard()
                )
                return
        
        if not text.strip():
            await update.message.reply_text(
                "❌ The file is empty.",
                reply_markup=get_main_keyboard()
            )
            return
        
        # Analyze the text
        result = analyze_text(text)
        
        if "error" in result:
            await update.message.reply_text(
                "❌ Could not analyze the text. Please try again.",
                reply_markup=get_main_keyboard()
            )
            return
        
        # Store for later
        context.user_data["last_text"] = text
        
        # Update stats
        data = get_user_data(str(update.effective_user.id))
        data["total_words"] += result["word_count"]
        data["total_chars"] += result["char_count"]
        data["total_analyses"] += 1
        
        formatted = format_analysis_result(result)
        await update.message.reply_text(
            formatted,
            parse_mode="Markdown",
            reply_markup=get_analysis_options_keyboard()
        )
        
    except Exception as e:
        print(f"Document error: {e}")
        await update.message.reply_text(
            "❌ Error processing the file. Please try again.",
            reply_markup=get_main_keyboard()
        )

# ==================== MAIN ====================

async def post_init(application):
    print("=" * 60)
    print(f"📊 {BOT_NAME} Started Successfully!")
    print(f"🤖 Username: @{BOT_USERNAME}")
    print(f"📦 Version: {BOT_VERSION}")
    print("=" * 60)
    print("✅ Bot is ready to analyze text!")
    print("=" * 60)

def main():
    print(f"🚀 Starting {BOT_NAME}...")
    print(f"📡 Using token: {BOT_TOKEN[:15]}...{BOT_TOKEN[-5:]}")
    
    application = ApplicationBuilder() \
        .token(BOT_TOKEN) \
        .post_init(post_init) \
        .build()
    
    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    
    # Callback handler
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    print("✅ Bot is polling for updates...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
