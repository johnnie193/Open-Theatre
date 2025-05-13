# Open-Theatre

An open-source interactive drama toolkit that enables dynamic interactive drama creation and character interaction through multiple AI architectures. 

Code for paper "Open-Theatre: An Open-Source Toolkit for LLM-based Interactive Drama".

## Features

- **Dynamic Script Creation**: Create and manage interactive stories with customizable scenes, characters, and plotlines
- **Multiple AI Architectures**:
  - v1 (One-for-All): Single LLM manages all character interactions
  - v2 (Director-Actor): Separate LLMs for director and character roles
  - v3 (Hybrid): Combines both architectures for enhanced storytelling
- **Character Management**:
  - Custom character profiles and avatars
  - Individual character memories and motivations
  - Dynamic character interactions
- **Scene Management**:
  - Flexible scene creation and editing
  - Scene-specific character motivations
  - Plotline management with detailed story branches
- **Real-time Interaction**:
  - Interactive chat interface
  - Dynamic response generation
  - Character memory tracking
- **Visual Customization**:
  - Custom character avatars
  - Adjustable interface layout
  - Modern and responsive design

## Technical Architecture

### Frontend
- Pure JavaScript for dynamic interactions
- Modular component structure
- Real-time UI updates
- Responsive CSS design

### Backend
- Python-based server
- LLM integration for character responses
- Memory management system
- Scene state tracking

## Getting Started

1. Clone the repository

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Add your OPENAI_KEY:
   You can create your .env file according to .env.example or set the client in utils/query_gpt4 function.

4. Start the server:
   ```bash
   python app.py
   ```
4. Access the web interface at `http://localhost:5000`

## Usage

1. **Create a New Script**:
   - Set script name and background narrative
   - Add characters with profiles
   - Define initial memories for characters

2. **Design Scenes**:
   - Create multiple scenes
   - Set scene-specific character motivations
   - Define plotlines and story branches
   - Choose AI architecture for each scene

3. **Start Interaction**:
   - Select characters to interact with
   - Input dialogue or actions
   - Watch the story unfold based on character responses

4. **Manage Progress**:
   - Track scene progression
   - Monitor character development
   - Export chat records

## Contributing

Contributions are welcome! Please feel free to submit pull requests or create issues for bugs and feature requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
