# ✨ Visual Journal Bot  
### *A Data Humanism & Giorgia Lupi–inspired Visual Storytelling Engine*  

This project transforms any kind of data — dreams, memories, routines, logs, spreadsheets, PDFs, office attendance, creative text — into intimate Data Humanism visualizations in the spirit of Giorgia Lupi’s “Dear Data.”

It generates a unique JSON visual specification using Gemini Flash, then renders it into a hand-drawn–style SVG postcard directly in the browser.

---

## 🌟 Features

### 💛 Data Humanism Visual Style  
- No dashboards, no charts  
- Soft, human, handmade-feeling visuals  
- Uses circles, lines, paths, repetition, spacing, small variations  
- Every dataset gets its own visual metaphor  

### 🧠 Gemini Flash Integration  
- Reads your data (text, PDF, spreadsheet, etc.)  
- Understands patterns  
- Creates JSON visual spec  
- Renderer converts JSON → SVG  

### 📂 Multi-Format Inputs  
Supports text, PDF, DOCX, CSV, XLSX.  
Works for dreams, memories, routines, logs, creative writing, emotional journals.

### 🎨 Unlimited Shapes & Styles  
Circles, lines, polygons, paths, text, legends — fully generative.

---

## 📁 Project Structure

visual-journal-bot/  
- app.py  
- gemini_client.py  
- data_parser.py  
- visual_spec_generator.py  
- renderer.py  
- prompts/system_prompt.txt  
- requirements.txt  
- README.md  

---

# 🚀 How It Works

1. User uploads text or a file  
2. `data_parser.py` extracts readable text  
3. Gemini Flash receives:
   - data type (dream/memory/etc.)  
   - extracted text  
   - meta description  
4. Gemini generates a JSON visual spec  
5. `renderer.py` converts it into SVG  
6. Streamlit displays it  
7. User downloads the postcard  

---

# 🔧 Install & Run

Clone the repo:
git clone https://github.com/yourusername/visual-journal-bot
cd visual-journal-bot

Create virtual environment:
python3 -m venv venv  
source venv/bin/activate  
(Windows: venv\Scripts\activate)

Install dependencies:
pip install -r requirements.txt

---

# 🔑 Gemini API Key Setup

Create a folder:
.streamlit

Inside it create:
secrets.toml

Add this line:
GEMINI_API_KEY = "your_api_key_here"

---

# ▶️ Run the App

streamlit run app.py

---

# 🖼 Example Workflow

- Upload a dream PDF / attendance sheet / routine log  
- Gemini produces layout, shapes, legend  
- Renderer produces Dear Data–style SVG  

---

# 🧰 Developer Notes

Extend renderer.py with more shapes: dashed paths, curves, blobs.  
Edit system_prompt.txt to tune metaphors, colors, legends.

To export PNG:
pip install cairosvg  
cairosvg visual.svg -o visual.png

---

# 📝 License
MIT License  

---

# 💛 Inspiration
Giorgia Lupi, Stefanie Posavec, Dear Data, Data Humanism

---

🎉 You're ready to create your own Data Humanism visual journals!
