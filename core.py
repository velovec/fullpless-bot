# coding=utf-8
from api import VKApi
from db import DBManager
from config import *
from time import sleep, time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re


class BotCore:

    def __init__(self):
        self._api = VKApi(VK_USER, VK_PASSWORD)
        self._user_id = self.get_user_id()

        self._db = DBManager()

        self._commands = {
            'publish': self.publish,
            'delayed_publish': self.delayed_publish
        }

    # VK API Methods

    def publish_post(self, message="", attachments=[]):
        response = self._api.call("wall.post", owner_id=COMMUNITY_ID, from_group=1,
                                  message=message, attachments=",".join(attachments), v=API_VERSION)

        if 'post_id' in response.keys():
            return response['post_id']

        return None

    def edit_post(self, post_id, message="", attachments=[]):
        return self._api.call("wall.edit", owner_id=COMMUNITY_ID, post_id=post_id,
                              message=message, attachment=",".join(attachments), v=API_VERSION)

    def get_post_likes(self, post_id):
        response = self._api.call("wall.getById", posts="%s_%s" % (COMMUNITY_ID, post_id), v=API_VERSION)

        if len(response) > 0 and 'likes' in response[0].keys():
            return response[0]['likes']['count']

        return 0

    def delete_post(self, post_id):
        return self._api.call("wall.delete", owner_id=COMMUNITY_ID, post_id=post_id, v=API_VERSION)

    def get_messages(self):
        response = self._api.call("messages.get")

        if len(response) > 1:
            for message in response[1:]:
                if message['read_state'] == 0 and message['out'] == 0:
                    self.process_message(message)
                    self.mark_message_as_read(message['mid'])

    def get_user_id(self):
        response = self._api.call("users.get")

        if len(response) > 0 and 'uid' in response[0].keys():
            return response[0]['uid']

    def send_message(self, user_id, message, attachments=[]):
        self._api.call("messages.send", peer_id=user_id, message=message,
                       attachment=",".join(attachments), v=API_VERSION)

    def upload_video(self, video_file, title, description=""):
        response = self._api.call("video.save", name=title, description=description,
                                  group_id=COMMUNITY_ID.replace('-',''), v=API_VERSION)

        if 'upload_url' in response.keys():
            self._api.upload_video(response['upload_url'], video_file)
            return response['owner_id'], response['video_id']

        return None, None

    def mark_message_as_read(self, message_id):
        self._api.call("messages.markAsRead", message_ids=message_id, v=API_VERSION)

    # Selenium Methods

    def publish_video(self, owner_id, video_id):
        driver = webdriver.Remote(command_executor=SELENIUM_HUB,
                                  desired_capabilities=webdriver.DesiredCapabilities.CHROME)
        wait = WebDriverWait(driver, 15)

        # Auth
        driver.get("https://vk.com")
        title = driver.title
        driver.find_element_by_css_selector('#index_email').send_keys(VK_USER)
        driver.find_element_by_css_selector('#index_pass').send_keys(VK_PASSWORD)
        driver.find_element_by_css_selector('#index_login_button').click()
        wait.until_not(lambda driver: driver.title == title)

        # Publish
        driver.get("https://vk.com/video%s_%s" % (owner_id, video_id))

        publish_button = '#mv_publish > table > tbody > tr > td.mv_publish_buttons > ' \
                         'button.mv_publish_add_btn.flat_button.fl_r'

        submit_button = '#box_layer > div.popup_box_container > div > div.box_controls_wrap > ' \
                        'div > table > tbody > tr > td > button'

        try:
            wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, publish_button))).click()
            wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, submit_button))).click()
            wait.until_not(EC.visibility_of_element_located((By.CSS_SELECTOR, submit_button)))
        except Exception, e:
            print "ERROR: Unable to publish video: " + str(e)
        finally:
            driver.close()

    # Bot Methods

    def publish_post_videos(self, post_id):
        for post_video in self._db.select("post_videos", post_id=post_id):
            video = self._db.select("videos", id=post_video[2])[0]
            self.publish_video(video[1], video[2])

    def get_post_videos(self, post_id):
        videos = []
        for post_video in self._db.select("post_videos", post_id=post_id):
            video = self._db.select("videos", id=post_video[2])[0]

            videos.append("video%s_%s" % (video[1], video[2]))

        return videos

    def get_post_documents(self, post_id):
        documents = []
        for post_documents in self._db.select("post_documents", post_id=post_id):
            document = self._db.select("documents", id=post_documents[2])[0]

            documents.append("doc%s_%s" % (document[3], document[4]))

        return documents

    def process_message(self, message):
        if message['uid'] in ADMIN_LIST:
            if ' ' in message['body']:
                cmd, message_body = message['body'].split(' ', 1)
            else:
                cmd, message_body = message['body'], None

            message['body'] = message_body

            if cmd in self._commands.keys():
                self._commands[cmd](message)
            else:
                self.send_message(message['uid'], "Неизвестная команда: %s. "
                                                  "Посмотреть список команд можно с помощью команды help." % cmd)

    def delayed_publish(self, message):
        if ' ' not in message['body']:
            self.send_message(message['uid'], "Команда delayed_publish требует как минимум 2 аргумента.\n"
                                              "delayed_publish время_публикации количество_лайков [текст_сообщения]")
            return

        delay, message_body = message['body'].split(' ', 1)
        message['body'] = message_body

        if re.match('^([0-9]{1,2}:)?([0-5]?[0-9])$', delay):
            if ':' in delay:
                hours, minutes = delay.split(':')
            else:
                hours, minutes = '0', delay

            delay = int(hours) * 60 + int(minutes)

            self.publish(message, delay=delay)
        else:
            self.send_message(message['uid'], "Время до публикации отложенной записи указано не верно. "
                                              "Формат: [ЧЧ:]ММ. Максимальное время отложенной публикации: 99:59")

    def publish(self, message, delay=0):
        if ' ' in message['body']:
            likes, message_text = message['body'].encode('utf-8').split(' ', 1)
        else:
            likes, message_text = message['body'], ""

        try:
            likes = int(likes)
        except ValueError:
            likes = 0

        documents = []
        videos = []

        if 'attachments' in message.keys():
            for attachment in message['attachments']:
                if attachment['type'] == 'doc':
                    documents.append(attachment['doc'])
                elif attachment['type'] == 'video':
                    videos.append(attachment['video'])

        if len(documents) == 0 or len(videos) == 0:
            self.send_message(message['uid'], "Вы забыли прикрепить видео или GIF-анимацию.")
            return

        self._db.insert("posts", likes=likes, message=message_text.decode('utf-8'), author=message['uid'],
                        published=False, got_likes=False, publish_at=int(time()) / 60 + delay)
        post_id = self._db.get_last_id("posts")

        for document in documents:
            result = self._db.select("documents", src_owner_id=document['owner_id'], src_document_id=document['did'])
            if len(result) == 0:
                request = {key: document[key] for key in ["owner_id", "did", "access_key"] if key in document.keys()}
                response = self._api.call("docs.add", **request)

                self._db.insert("documents", src_owner_id=document['owner_id'], src_document_id=document['did'],
                                owner_id=self._user_id, document_id=response)
                self._db.insert("post_documents", post_id=post_id, document_id=self._db.get_last_id("documents"))
            else:
                self._db.insert("post_documents", post_id=post_id, document_id=result[0][0])

        for video in videos:
            result = self._db.select("videos", owner_id=video['owner_id'], video_id=video['vid'])
            if len(result) == 0:
                self._db.insert("videos", owner_id=video['owner_id'], video_id=video['vid'])
                self._db.insert("post_videos", post_id=post_id, video_id=self._db.get_last_id("videos"))
            else:
                self._db.insert("post_videos", post_id=post_id, video_id=result[0][0])

        if delay > 0:
            self.send_message(message['uid'], "Публикация записи отложена на %02d:%02d" % (delay / 60, delay % 60))

    def check_posts(self):
        for post in self._db.select("posts"):
            if not post[5] and post[7] <= int(time()) / 60:
                attachments = self.get_post_documents(post[0])

                if post[2] == 0:
                    self.publish_post_videos(post[0])
                    attachments += self.get_post_videos(post[0])

                post_id = self.publish_post(post[4].encode('utf-8'), attachments=attachments)
                self._db.update("posts", post[0], post_id=post_id, published=True, got_likes=post[2] == 0)
                self.send_message(post[3], "Запись опубликована."
                                           "" + ("" if post[2] == 0 else " Требуемое количество лайков: %d" % post[2]))
            elif post[5] and not post[6] and post[2] <= self.get_post_likes(post[1]):
                attachments = self.get_post_documents(post[0])

                self.publish_post_videos(post[0])
                attachments += self.get_post_videos(post[0])
                self.edit_post(post[1], message=post[4].encode('utf-8'), attachments=attachments)
                self._db.update("posts", post[0], got_likes=True)

                self.send_message(post[3], "Запись собрала требуемое количество лайков. "
                                           "Видео опубликовано.", attachments=self.get_post_documents(post[0]))

    def run(self):
        try:
            while True:
                self.get_messages()
                self.check_posts()
                sleep(30)
        except KeyboardInterrupt:
            print "Shutting down bot..."
        finally:
            self._db.close()


if __name__ == "__main__":
    bot = BotCore()

    bot.run()
