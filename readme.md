# 1Password Duplicate Item Archiver

1Password used to have a tool to help you find and remove duplicates, but they removed it. This is a simple script that uses the 1Password CLI to find and archive duplicates.

UPDATE: They've added a dupe finder to the Watchtower in the latest beta, hopefully rendering this obsolete: https://1password.community/discussion/comment/697252/#Comment_697252


## Getting Started

1. **Clone this repository**:
   ```bash
   git clone https://github.com/Taytay/1password_utils.git
   cd 1password_utils
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python3 -m venv venv # Use python if you don't have python3 in PATH
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. **Install requirements**:
   ```bash
   pip install -r requirements.txt
   ```


4. **Run the script**:
   ```bash
   ./dupe.py
   ```

   - If you already know the vault name, you can do:
     ```bash
     ./dupe.py MyVault
     ```

   - Or just let the script prompt you to select an account and vault interactively.

