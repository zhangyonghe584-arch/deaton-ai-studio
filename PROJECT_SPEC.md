# Deaton AI Studio Product Specification


## Overview

Deaton AI Studio is a desktop AI-assisted automotive case production system.

Created for:

Deaton Auto


Purpose:

Convert automotive programming cases into professional images and videos.


---

# Main Workflow


User:

1. Upload vehicle images
2. Upload videos
3. Fill case information


Software:

1. Manage project
2. Analyze materials
3. Generate production plan
4. Create images/videos
5. Export final result


---

# Main Modules


## 1. Dashboard


Show:

- Current project
- Recent cases
- Production status


---

## 2. Image Case Module


Functions:

- Drag and drop upload
- Six category management
- Image preview
- Delete
- Sort
- AI analysis


Categories:


01 Vehicle Exterior

02 Fault Symptoms

03 Diagnosis / Equipment Connection

04 Programming Process

05 Completed Result

06 Technical Materials



---

## 3. Video Case Module


Functions:


- Upload videos
- Preview videos
- Add text
- Generate case videos


---

## 4. Case Information Module


No TXT file.


Use professional form.


Information:


Vehicle Brand

Model

Year

Region

Fault Category

Service Type

Programming Type

Equipment Used

Repair Result



Save:

project.json


---

## 5. AI Assistant


Use OpenAI API.


Functions:


- Understand images
- Analyze case
- Suggest production style
- Generate text
- Optimize layout


AI should assist.

User makes final decision.


---

## 6. Production Engine


Image:

- Multiple templates
- Brand logo
- Professional automotive style


Video:

- Text overlay
- Case introduction
- Professional editing


---

## 7. Settings


Include:


API Key

Model Selection

Template Management

Output Path


---

# Final Goal


A Windows desktop application.

User should only need:

Upload materials

↓

AI assistance

↓

Review result

↓

Export finished content