# IT-359-Project
Our project for this course will be an ethical keylogging software. This will allow us to save keystrokes to a .txt file and read user inputs on infected machines remotely.

## Team Members
- Cameron Trojan
- Justin Walinski

## Full Project Idea
Our team will create a keylogging software that will allow us to read user inputs on a specified machine. This will allow us to read information from a machine
remotely and access the data associated with the user inputs. For this project, we will be focusing on the educational aspect of keylogging software, detection,
and countermeasures to combat key loggers. We will utilise the ISU Suhsi AI models to help with file analysis and creation of baseline code for our starting point.
Beyond baseline creation, the AI model will serve as the primary tool for log and telemetry analysis. By processing our software .txt files through these models
we will be able to easily recognize and understand patterns, diagnose anomalies, and gain a deeper understanding of the system behavior.
# Key components
- TXT file to store key strokes
- Exportable code to a USB drive for portability
- Software transmission (Phishing or physical hardware)
- Timestamps relating to the logged information (MM/DD)
- Interval screenshots
- Website activity

# Instructions
- Once downloaded, the .py file can be run from an IDE or a CMD prompt.
- Once the program is started (.py), there will be output in the kernel relating to the OS,
  and **a file titled data.txt will be created** somewhere on your system. This .txt file will contain all information captured
  while the program is running. Data will show website activity and all keys pressed until the Enter key is pressed.
- If the program is started via the .exe, there will be no notification of the program running. The data.txt file will be created.
- Every time the screen changes (Active window changes), a screenshot will be taken and **stored in a folder titled "Screenshots".**
- To terminate the program, either end the process from the CMD shell or the IDE.
- To terminate the .exe program, enter Task Manager and locate the .exe.

# Dependencies
This program will require multiple dependencies to function properly. Please install these using pip to use the program.
- keyboard
- mss
- pillow
- pywin32
- netifaces
