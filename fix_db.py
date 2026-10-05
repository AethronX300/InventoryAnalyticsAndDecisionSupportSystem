import sqlite3
import json
conn = sqlite3.connect('meridian.db')
conn.execute("UPDATE app_settings SET value = '\"₹\"' WHERE key = 'currency'")
conn.commit()
conn.close()
