import os

VK_USER = os.getenv('VK_USER')
VK_PASSWORD = os.getenv('VK_PASSWORD')

COMMUNITY_ID = os.getenv('COMMUNITY_ID', '-160646006')
API_VERSION = os.getenv('API_VERSION', '5.71')
ADMIN_LIST = [int(user_id) for user_id in os.getenv('ADMIN_LIST', '469063957,13450201').split(',')]
SELENIUM_HUB = os.getenv('SELENIUM_HUB', 'http://172.17.0.1:4444/wd/hub')