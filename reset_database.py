from database import engine
from models import Base

def reset_database():
    # Option for deleteing all tables and rebuild new tables
    confirm = input('Are you sure you want to continue to delete all tables and rebuild? (Type "yes" to continue): ')
    if confirm.lower() != 'yes':
        print("Operation cancelled.")
        return

    # Delete all tables
    Base.metadata.drop_all(engine)
    print("All tables have been deleted.")

    # Recreate tables based on the latest models.py.
    Base.metadata.create_all(engine)
    print("The table has been rebuilt based on the latest model.")

if __name__ == "__main__":
    reset_database()