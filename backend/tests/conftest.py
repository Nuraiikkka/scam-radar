"""Use the test DB even when only one test module is selected."""
import os

os.environ['SCAMRADAR_DATABASE_URL'] = 'sqlite:///./test.db'
os.environ['SCAMRADAR_MOCK'] = 'false'
