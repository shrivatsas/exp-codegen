import pyotp
import pickle
import os
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer

class User:
    def __init__(self, username, secret):
        self.username = username
        self.secret = secret

class TOTPLoginApp:
    def __init__(self):
        self.users = {}
        self.data_file = 'users.pkl'
        self.load_users()

    def load_users(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'rb') as f:
                self.users = pickle.load(f)

    def save_users(self):
        with open(self.data_file, 'wb') as f:
            pickle.dump(self.users, f)

    def register_user(self, username):
        if username in self.users:
            print("User already exists.")
            return

        secret = pyotp.random_base32()
        self.users[username] = User(username, secret)
        self.save_users()

        totp = pyotp.TOTP(secret)
        print(f"User registered successfully. Your secret key is: {secret}")
        print(f"Your current TOTP code is: {totp.now()}")
        
        self.generate_qr_code(username, secret)

    def generate_qr_code(self, username, secret):
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(username, issuer_name="TOTPLoginApp")

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white", image_factory=StyledPilImage, module_drawer=RoundedModuleDrawer())
        
        # Save the QR code image
        img_path = f"{username}_qr.png"
        img.save(img_path)
        print(f"QR code saved as {img_path}")

        # Display ASCII QR code in terminal
        qr.print_tty()
        print("Scan this QR code with your authenticator app or use the secret key.")

    def login(self, username, totp_code):
        if username not in self.users:
            print("User not found.")
            return False

        user = self.users[username]
        totp = pyotp.TOTP(user.secret)

        if totp.verify(totp_code):
            print("Login successful!")
            return True
        else:
            print("Invalid TOTP code.")
            return False

def main():
    app = TOTPLoginApp()

    while True:
        print("\n1. Register")
        print("2. Login")
        print("3. Exit")
        choice = input("Enter your choice (1-3): ")

        if choice == '1':
            username = input("Enter username: ")
            app.register_user(username)
        elif choice == '2':
            username = input("Enter username: ")
            totp_code = input("Enter TOTP code: ")
            app.login(username, totp_code)
        elif choice == '3':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
