import mysql.connector
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

def get_db_config():
    """Retourne le dictionnaire de configuration (utile pour tes classes Test)"""
    return {
        'host': os.getenv('DB_HOST'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'database': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD')
    }

def get_db_connection():
    """Connexion directe via mysql-connector (ton code original)"""
    config = get_db_config()
    return mysql.connector.connect(**config)

def get_engine():
    """Crée l'engine SQLAlchemy nécessaire pour pd.read_sql()"""
    config = get_db_config()
    return create_engine(
        f"mysql+mysqlconnector://{config['user']}:{config['password']}@"
        f"{config['host']}:{config['port']}/{config['database']}"
    )

engine = get_engine()