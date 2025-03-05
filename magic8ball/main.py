# A Magic 8 Ball app that gives random answers to questions. It uses Pygame for sound effects and PyQt for the GUI. 
# The ball shakes and displays a random answer after a delay. The answer text has a gradient effect for style.
# ----------------------------------------------------------------------------------------------------------------------

# Import necessary modules
import os
import sys
import random
import pygame  # For sound effects
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit
from PyQt6.QtGui import QFont, QPixmap, QMovie
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QRect


# Predefined Magic Rude Ball responses
RESPONSES = ALL_RESPONSES = [
    "Yes, definitely.",
    "No, not at all.",
    "Ask again later.",
    "It is certain.",
    "Very doubtful.",
    "Without a doubt.",
    "Cannot predict now.",
    "Absolutely!",
    "No chance.",
    "Signs point to yes.",
    "LOL, good luck with that.",
    "Try again… after therapy.",
    "Even your cat knows the answer is NO.",
    "I consulted the spirits… they laughed.",
    "Bruh, you really need me to answer that?",
    "Did you really just ask that?",
    "LMAO, absolutely not.",
    "Yeah, sure, in an alternate universe.",
    "Let me think… nah.",
    "Just do it! YOLO, baby!",
    "Hold my beer… nope.",
    "Ask me when I’m sober. (Never happening.)",
    "If bad decisions were a sport, you’d be winning.",
    "Sure, but only if you bring tequila.",
    "Whiskey says yes, common sense says no.",
    "You can… but should you?",
    "Not even Tinder would swipe right on that idea.",
    "Go for it! What's the worst that could happen? (Don’t answer that.)",
    "You might need a lawyer for that.",
    "Only if you want a regret-filled morning.",
    "If you're asking, you already know it's a bad idea.",
    "Uhh… pass.",
    "Google it, I'm on break.",
    "I'm on vacation, ask again later.",
    "Not my problem, dude.",
    "Why not? Screw it.",
    "Meh, do whatever."


]

# Predefined text colors for answers (for gradient effect)
TEXT_COLORS = ["#FF5733", "#33FF57", "#3357FF", "#FFD700", "#FF1493", "#8A2BE2", "#00FA9A", "#FF4500", "#FF00FF", "#00FFFF"]


# Function to get the resource path for PyInstaller
def resource_path(relative_path):
    """ Get the absolute path to a resource, compatible with PyInstaller """
    if getattr(sys, 'frozen', False):  # Running as an executable
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# Main application class for the Magic 8 Ball
class Magic8BallApp(QWidget):
    def __init__(self):
        super().__init__()

        # Window setup and styling 
        self.setWindowTitle("Magic 8 Ball")
        self.setGeometry(100, 100, 400, 500) # x, y, width, height
        self.setStyleSheet("background-color: #222244;") 

        # Initialize sound effect
        pygame.mixer.init()
        self.sound = pygame.mixer.Sound(resource_path("magic8sound.mp3"))

        # Layout for the app
        layout = QVBoxLayout()

        # Label for instructions 
        self.label = QLabel("Ask the Magic 8 Ball a question:")
        self.label.setFont(QFont("Arial", 14))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        # Input box for question 
        self.input_box = QLineEdit(self)
        self.input_box.setStyleSheet(
            "background-color: #444466; color: white; border-radius: 8px; padding: 5px;"
        )

        # Set font and size for input box 
        self.input_box.setFont(QFont("Arial", 12))
        layout.addWidget(self.input_box)

        #  Container for the ball image 
        self.ball_container = QWidget(self)
        self.ball_container.setFixedSize(200, 200)
        layout.addWidget(self.ball_container, alignment=Qt.AlignmentFlag.AlignCenter)

        # 8Ball image inside the container
        self.ball_label = QLabel(self.ball_container)
        self.ball_pixmap = QPixmap(resource_path("magic8ball.png"))
        self.ball_pixmap = self.ball_pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio)
        self.ball_label.setPixmap(self.ball_pixmap)
        self.ball_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Spinning text inside the ball container 
        self.spinning_text = QLabel("", self.ball_container)
        self.spinning_text.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.spinning_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spinning_text.setStyleSheet("color: white;")
        self.spinning_text.setGeometry(50, 80, 100, 40)
        self.spinning_text.hide()

        # Button to ask the question
        self.button = QPushButton("Ask Anything!")
        self.button.setStyleSheet("""
            QPushButton {
                background-color: #FF5733;  /* Vibrant orange */
                color: white;
                border-radius: 10px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF4500;  /* Slightly darker on hover */
            }
        """)

        # Set font and size for button 
        self.button.setFont(QFont("Arial", 12))
        self.button.clicked.connect(self.start_animation)
        layout.addWidget(self.button)

        # Label for the answer 
        self.answer_label = QLabel("")
        self.answer_label.setFont(QFont("Arial", 14))
        self.answer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.answer_label.setStyleSheet("color: white; background-color: black; padding: 10px; border-radius: 10px;")
        self.answer_label.hide()  # Hide answer initially
        layout.addWidget(self.answer_label)

        # Set layout for the app
        self.setLayout(layout)

    # Function to start the animation 
    def start_animation(self):
        """Starts the ball animation before revealing the answer"""
        question = self.input_box.text().strip()
        if not question:
            self.answer_label.setText("Please ask a question!")
            self.answer_label.show()
            return

        # Add shaking effect to the ball image
        self.shake_ball()

        # Show spinning text while thinking
        self.spinning_text.setText("Thinking...")
        self.spinning_text.show()
        self.pulse_text()

        # Add glowing effect to the ball image 
        glow_colors = ["cyan", "magenta", "yellow", "lime", "orange", "pink", "blue", "purple", "red", "green"]
        random_glow = random.choice(glow_colors)
        self.ball_label.setStyleSheet(f"border: 5px solid {random_glow}; border-radius: 100px;")


        # Delay before showing the answer
        QTimer.singleShot(2000, self.show_answer)  # 2-second delay before revealing answer

    # Function to shake the ball 
    def shake_ball(self):
        """Shakes the ball before revealing the answer"""
        self.shake_animation = QPropertyAnimation(self.ball_label, b"geometry")
        self.shake_animation.setDuration(500)  # Shake duration
        self.shake_animation.setKeyValueAt(0, QRect(self.ball_label.x(), self.ball_label.y(), 200, 200))
        self.shake_animation.setKeyValueAt(0.25, QRect(self.ball_label.x() - 5, self.ball_label.y(), 200, 200))
        self.shake_animation.setKeyValueAt(0.5, QRect(self.ball_label.x() + 5, self.ball_label.y(), 200, 200))
        self.shake_animation.setKeyValueAt(0.75, QRect(self.ball_label.x() - 5, self.ball_label.y(), 200, 200))
        self.shake_animation.setKeyValueAt(1, QRect(self.ball_label.x(), self.ball_label.y(), 200, 200))
        self.shake_animation.start()

    # Function to pulse the text 
    def pulse_text(self):
        """Makes the spinning text pulse in size"""
        self.pulse_animation = QPropertyAnimation(self.spinning_text, b"font")
        self.pulse_animation.setDuration(500)  # Pulse duration
        self.pulse_animation.setKeyValueAt(0, QFont("Arial", 18, QFont.Weight.Bold))
        self.pulse_animation.setKeyValueAt(0.5, QFont("Arial", 24, QFont.Weight.Bold))
        self.pulse_animation.setKeyValueAt(1, QFont("Arial", 18, QFont.Weight.Bold))
        self.pulse_animation.setLoopCount(2)  # Repeat twice
        self.pulse_animation.start()

    # Function to show the answer 
    def show_answer(self):
        """Displays the random answer after animation"""
        # Hide spinning text
        self.spinning_text.hide()

        # Choose a random color for the answer text
        random_color = random.choice(TEXT_COLORS)
        gradient_style = f"""
            color: white;  /* Ensures maximum contrast */
            font-weight: bold;  /* Makes text stand out */
            font-size: 18px;  /* Slightly larger for readability */
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.6); /* Adds a shadow for depth */
            background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, 
                        stop:0 #222244, stop:1 {random_color});
            padding: 15px;
            border-radius: 10px;
        """

        # Apply gradient style to answer text
        self.answer_label.setStyleSheet(gradient_style)


        # Display answer
        self.answer_label.setText(random.choice(RESPONSES))
        self.answer_label.show()

        # Remove glowing effect
        self.ball_label.setStyleSheet("")

        # Play sound effect
        self.sound.play()

# Main function to run the app
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Magic8BallApp()
    window.show()
    sys.exit(app.exec()) # Run the application
