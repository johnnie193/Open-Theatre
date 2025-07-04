# 🎭 OPEN-THEATRE

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Demo Video](https://img.shields.io/badge/Demo-YouTube-red.svg)](https://www.youtube.com/watch?v=iN1Q3z24-LY)

**An Open-Source Toolkit for LLM-based Interactive Drama**

*Code repository for the paper "OPEN-THEATRE: An Open-Source Toolkit for LLM-based Interactive Drama"*

[🎬 Demo Video](https://www.youtube.com/watch?v=iN1Q3z24-LY) • [🚀 Quick Start](#quick-start) • [🏗️ Architecture](#architecture)

</div>

---

## 📖 Overview

**OPEN-THEATRE** is a cutting-edge, open-source toolkit that revolutionizes interactive drama creation through advanced Large Language Model (LLM) architectures. Our system enables dynamic storytelling with intelligent character interactions, sophisticated memory systems, and multiple AI coordination strategies.

### 🌟 Key Highlights

- 🎯 **Multiple AI Architectures**: Four distinct coordination strategies for different storytelling needs
- 🧠 **Advanced Memory System**: Sophisticated character memory with retrieval-augmented generation (RAG)
- 🎭 **Intelligent Character Agents**: Autonomous player agents with customizable personas
- 🌐 **Modern Web Interface**: Intuitive, responsive UI for seamless interaction
- 🔧 **Extensible Framework**: Modular design supporting multiple LLM providers

![Interactive Drama Demo](doc/interactive_drama.png)
*Figure 1: A demonstration of LLM-based interactive drama. The script is adapted from the popular anime Detective Conan.*

---

## 🏗️ Architecture

### 🎪 AI Coordination Architectures

Our toolkit supports four distinct AI architectures, each optimized for different storytelling scenarios:

| Architecture | Mode | Description | Best For |
|-------------|------|-------------|----------|
| 🎯 **One-for-All** | `v1` | Single LLM manages all characters | Simple scenarios, consistent tone |
| 🎬 **Director-Actor** | `v2_plus` | Separate director and character LLMs | Complex multi-character scenes |
| 🌐 **Director-Global-Actor** | `v2_prime` | Global director with specialized actors | Large-scale narratives |

### 🧠 Memory System Architecture

![Memory Workflow](doc/memory_workflow.png)
*Figure 2: Hierarchical Memory Architecture. New dialogues are ingested into the Event Store and call the retriever to query all stores. The scene transition signal calls the summarizer module to create new entries in the Summary Store and move original records to the Archive Store, completing the memory lifecycle.*

Our sophisticated memory system features:
- **📚 Hierarchical Memory Storage**: Four specialized stores (Global, Event, Summary, Archive) organize memory for efficient, scene-based, and character-specific recall.
- **🔍 Dynamic Semantic Retrieval**: A unique scoring model combines hybrid relevance (lexical + semantic) with dynamic importance, ensuring highly relevant memory recall. 
- **📝 Memory Summarization**: Our summarizer actively manages cognitive load through memory consolidation, generating abstractive summaries of completed scenes, and moving original detailed records to an long-term archive. 
---

## 🚀 Quick Start

### 📋 Prerequisites

- Python 3.12
- LLM API access (Azure OpenAI, OpenAI, or DeepSeek)

### ⚡ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/Open-Theatre.git
   cd Open-Theatre
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Launch the application**
   ```bash
   python main.py
   ```

5. **Access the interface**
   Open `http://127.0.0.1:3000` in your browser

### 🎬 Demo Video

Watch our comprehensive setup and usage demo: [**YouTube Demo**](https://www.youtube.com/watch?v=iN1Q3z24-LY)

---

## 🎮 User Interface

![User Interface](doc/view_panel.png)
*Figure 3: Modern, intuitive web interface for interactive drama creation and management*

### 🎨 Interface Features

- **📝 Script Editor**: Visual script creation with drag-and-drop components
- **👥 Character Manager**: Comprehensive character profile and avatar management
- **🎬 Scene Designer**: Interactive scene creation with motivation and plotline tools
- **💬 Real-time Chat**: Dynamic conversation interface with character responses
- **📊 Analytics Dashboard**: Performance metrics and interaction statistics
- **🎯 Memory Viewer**: Real-time memory state visualization

---

## 🔧 Configuration

### 🌐 LLM Provider Setup

Configure your preferred LLM provider in `.env`:

```env
# Choose your provider: azure_openai, openai, deepseek
LLM_PROVIDER=azure_openai

# Azure OpenAI Configuration
AZURE_API_KEY=your_azure_api_key
AZURE_ENDPOINT=https://your-instance.openai.azure.com/
AZURE_DEPLOYMENT=gpt-4o
AZURE_API_VERSION=2024-08-01-preview

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o

# DeepSeek Configuration
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_API_URL=https://api.deepseek.com
DEEPSEEK_MODEL=DeepSeek-V3

# System Configuration
ENGLISH_MODE=false
STORAGE_MODE=true
```

### ⚙️ Advanced Configuration

```env
# Memory System
MEMORY_SIMILARITY_THRESHOLD=0.7
MAX_RETRIEVED_MEMORIES=5
MEMORY_DECAY_FACTOR=0.9

# Performance Optimization
ASYNC_MODE=true
PARALLEL_PROCESSING=true
CACHE_ENABLED=true
```

---

## 🤖 PlayerAgent System

### 🎯 Intelligent Player Simulation

Our **PlayerAgent** system provides autonomous player simulation with sophisticated decision-making capabilities:

```python
import asyncio
from player_agent import PlayerAgent

async def demo_intelligent_player():
    # Initialize PlayerAgent with specific persona
    agent = PlayerAgent(llm_provider="azure_openai")

    # Run automated session with intelligent interactions
    records = await agent.auto_play_session(
        script_path="script/Romeo and Juliet_eng.yaml",
        mode="v2_plus",
        num_interactions=10,
        persona_type="university_student",  # Specific character persona
        use_intelligent_interaction=True
    )

    # Export detailed interaction records
    export_path = agent.export_records("romeo_juliet_session.json")
    print(f"Session exported to: {export_path}")

asyncio.run(demo_intelligent_player())
```

### 🎭 Persona-Based Interactions

Choose from predefined personas or create custom ones:

| Persona | Characteristics | Interaction Style |
|---------|----------------|-------------------|
| 🎓 **University Student** | Curious, analytical, questioning | Asks probing questions, seeks understanding |
| 💼 **Office Worker** | Practical, efficient, goal-oriented | Focuses on solutions and outcomes |
| 📚 **High School Student** | Energetic, social, emotional | Expressive reactions, peer-focused |
| 👨‍🏫 **Retired Teacher** | Wise, patient, observant | Thoughtful responses, guidance-oriented |
| 💻 **Freelancer** | Creative, independent, adaptable | Innovative approaches, flexible thinking |

### 📊 Performance Analytics

```python
# Get detailed statistics
stats = agent.get_statistics()
print(f"Success Rate: {stats['success_rate']}%")
print(f"Average Response Time: {stats['average_response_time']}s")
print(f"Total Interactions: {stats['total_interactions']}")
```

---

## 🎨 Script Creation

### 📝 YAML-Based Script Format

Create rich, interactive stories using our intuitive YAML format:

```yaml
id: Romeo and Juliet
background:
  player: Romeo
  narrative: |
    The story revolves around Romeo, the only son of the Montague family. 
  characters:
    Romeo: The only son of the Montague family, emotionally rich and conflicted, often troubled by his family’s feuds and his love life.
    Montague: A serious and resilient middle-aged man, Romeo’s father, the leader of the Montague family, long-time enemy of the Capulet family.
    Lady Montague: Gentle and kind, Romeo’s mother, deeply concerned about her son’s emotional changes.
    Benvolio: Calm, kind, and helpful, a peacekeeper who adheres to rules, Romeo’s cousin and thoughtful friend.
    Juliet: Romeo’s love interest, the only daughter of the Capulet family, intelligent and strong but also troubled by the family feud.
scenes:
  scene1:
    name: Dawn in Verona Square
    mode: v1
    scene: Location:Verona Square. Time:10 AM. Romeo is walking alone, trying to clear his mind, and spots his parents—the Montague couple. 
    characters:
      Romeo: 
      Montague: Aware of the ongoing conflict with the Capulet family’s servants, concerned about Romeo’s mood, asks Benvolio to talk to him.
      Lady Montague: Aware of the ongoing conflict with the Capulet family’s servants, concerned about Romeo’s mood, asks Benvolio to talk to him.
      Benvolio: Resolves the dispute between the Montague and Capulet servants, tries to console Romeo.
    chain:
    - The Montagues and Benvolio meet in the square, Montague asked Benvolio to console Romeo.
    - Benvolio talks to Romeo about his emotional troubles.
    - Romeo and Benvolio discuss whether he is too obsessed with his feelings.
    stream:
      The Montagues and Benvolio meet in the square, Montague asked Benvolio to console Romeo.:
        - Montague:(angrily adjusting his sleeves) Who started this again? Who is rekindling the feud between our families this early in the morning?
        - Benvolio:I saw their servants fighting as soon as I arrived. I had to step in to separate them.
      Benvolio talks to Romeo about his emotional troubles.:
        - Benvolio:Romeo. I heard you’ve been troubled by matters of the heart. How are you now?
        - Romeo:(pauses, sighs) I... I am consumed by love, unable to escape this pain. She won’t look at me.
```

### 🎬 Scene Management

- **🎯 Flexible Modes**: Choose optimal AI architecture per scene
- **📋 Character Motivations**: Scene-specific character goals and behaviors
- **📖 Plotline Tracking**: Multi-threaded story progression
- **🔄 Dynamic Transitions**: Intelligent scene flow management

---

### 🧩 Modular Architecture

```
Open-Theatre/
├── 🎭 frame.py              # Core drama engine
├── 🤖 player_agent.py       # Intelligent player simulation
├── 🧠 memory/               # Advanced memory system
├── 🎨 components/           # Frontend components
├── 📝 script/               # Story scripts
├── 🎯 prompt/               # LLM prompts
└── 🔧 models.py             # Multi-provider LLM management
```

---

## 🚀 Advanced Features

### ⚡ Asynchronous Processing

Leverage high-performance async processing for multi-character scenes:

```python
# Enable async mode for better performance
mode: v2_plus_async  # Up to 75% faster than synchronous processing
```

**Performance Benefits:**
- 🚀 **3x Faster**: Multi-character scenes with parallel LLM calls
- 💾 **Memory Efficient**: Optimized resource utilization
- 🔄 **Non-blocking**: Responsive user interface during processing

### 🧠 Advanced Memory Features

```python
# Configure memory system parameters in memory/base.py
LAYER_WEIGHTS = {
    "global": 1.0,
    "event": 1.0,
    "summary": 1.0,
}
TAG_WEIGHTS = {
    # setting layer
    "profile": 1.5,
    "scene_init": 1.3,
    "scene_objective": 1.4,

    # event_raw layer
    "conversation": 1.0,

    # event_summary layer
    "summary_conversation": 1.2,
    "summary_scene_init": 1.1,
    "summary_scene_objective": 1.3,

    # archived layer
    "archived_conversation": 0.2, 
    "archived_scene_init": 0.1,
    "archived_scene_objective": 0.1,
}
TAG_EMBEDDING_WEIGHT = 0.0
TEXT_WEIGHT = 1.0
IMPORTANCE_ADDITION_WEIGHT = 0.05
IMPORTANCE_ADDITION_THRESHOLD = 10
```

### 🌐 Multi-Language Support

- 🇺🇸 **English Mode**: Full English language support
- 🇨🇳 **Chinese Mode**: Native Chinese language processing
- 🔄 **Dynamic Switching**: Runtime language mode changes

---

## 🤝 Contributing

We welcome contributions from the community! If you have any questions or suggestions, please open an issue or contact us directly.

### 📋 Contribution Guidelines

1. **🐛 Bug Reports**: Use GitHub Issues with detailed reproduction steps
2. **✨ Feature Requests**: Propose new features with use cases and examples
3. **🔧 Pull Requests**: Follow our coding standards and include tests
4. **📖 Documentation**: Help improve documentation and examples

### 🎯 Areas for Contribution

- 🧠 **Memory System Enhancements**: Advanced retrieval algorithms
- 🎭 **New Character Archetypes**: Expand personality models
- 🌐 **Language Support**: Additional language implementations
- 🎨 **UI/UX Improvements**: Enhanced user interface features
- ...


---

## 📞 Support
- **📧 Email**: [johnnie.walker@sjtu.edu.cn](mailto:johnnie.walker@sjtu.edu.cn)
- **🐛 Issues**: [GitHub Issues](https://github.com/your-username/Open-Theatre/issues)
- **📖 Wiki**: [Community Wiki](https://github.com/your-username/Open-Theatre/wiki)

---

## 📜 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 OPEN-THEATRE Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

<div align="center">

**🎭 OPEN-THEATRE** - *Revolutionizing Interactive Drama with AI*

[![GitHub stars](https://img.shields.io/github/stars/your-username/Open-Theatre?style=social)](https://github.com/johnnie193/Open-Theatre/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/your-username/Open-Theatre?style=social)](https://github.com/johnnie193/Open-Theatre/network/members)

[⭐ Star us on GitHub](https://github.com/johnnie193/Open-Theatre) • [🎬 Watch Demo](https://www.youtube.com/watch?v=iN1Q3z24-LY)

</div>
