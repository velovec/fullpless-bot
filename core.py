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
        self._api = VKApi(VK_USER, VK_PASSWORD, version=API_VERSION)
        self._user = self.get_user()
        self._user_id = self._user['id']

        self._db = DBManager()

        self._commands = {
            'cancel': self.cancel,
            'publish': self.publish,
            'delayed_publish': self.delayed_publish
        }

        print "[INFO] Logged in as %s %s (UID: %s)" % (
            self._user['first_name'],
            self._user['last_name'],
            self._user_id
        )

    # VK API Methods

    def publish_post(self, message="", attachments=[]):
        response = self._api.call("wall.post", owner_id=COMMUNITY_ID, from_group=1,
                                  message=message, attachments=",".join(attachments))

        if 'post_id' in response.keys():
            return response['post_id']

        return None

    def edit_post(self, post_id, message="", attachments=[]):
        return self._api.call("wall.edit", owner_id=COMMUNITY_ID, post_id=post_id,
                              message=message, attachment=",".join(attachments))

    def get_post_likes(self, post_id):
        response = self._api.call("wall.getById", posts="%s_%s" % (COMMUNITY_ID, post_id))

        if len(response) > 0 and 'likes' in response[0].keys():
            return response[0]['likes']['count']

        return 0

    def delete_post(self, post_id):
        return self._api.call("wall.delete", owner_id=COMMUNITY_ID, post_id=post_id)

    def get_messages(self):
        response = self._api.call("messages.get", count=200)

        for message in response['items']:
            if message['read_state'] == 0 and message['out'] == 0:
                self.process_message(message)
                self.mark_message_as_read(message['id'])

    def get_user(self):
        response = self._api.call("users.get")

        if len(response) > 0 and 'id' in response[0].keys():
            return response[0]

    def send_message(self, user_id, message, attachments=[]):
        self._api.call("messages.send", peer_id=user_id, message=message,
                       attachment=",".join(attachments))

    def upload_video(self, video_file, title, description=""):
        response = self._api.call("video.save", name=title, description=description,
                                  group_id=COMMUNITY_ID.replace('-',''))

        if 'upload_url' in response.keys():
            self._api.upload_video(response['upload_url'], video_file)
            return response['owner_id'], response['video_id']

        return None, None

    def mark_message_as_read(self, message_id):
        self._api.call("messages.markAsRead", message_ids=message_id)

    def get_album(self, album_name, privacy='all'):
        for album in self._api.call("video.getAlbums", extended=True)['items']:
            if album['title'] == album_name:
                if privacy not in album['privacy']:
                    self._api.call("video.editAlbum", album_id=album['id'], privacy=privacy)

                return album['id']

        return self._api.call("video.addAlbum", title=album_name, privacy=privacy)['album_id']

    # Selenium Methods

    def publish_video(self, owner_id, video_id):
        driver = webdriver.Remote(command_executor=SELENIUM_HUB,
                                  desired_capabilities=webdriver.DesiredCapabilities.CHROME)
        wait = WebDriverWait(driver, 15)

        try:
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

            wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, publish_button))).click()
            wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, submit_button))).click()
            wait.until_not(EC.visibility_of_element_located((By.CSS_SELECTOR, submit_button)))
        except Exception, e:
            print "[ERROR] Unable to publish video: " + str(e)
        finally:
            driver.close()

    # Bot Commands

    def cancel(self, message):
        try:
            post_id = int(message['body'])
        except ValueError:
            self.send_message(message['user_id'], "Команда cancel требует аргумент.\n"
                                                  "cancel post_id")
            return

        posts = self._db.select("posts", id=post_id, published=False)
        if len(posts) > 0:
            self._db.delete("posts", id=post_id)
            self._db.delete("post_attachments", post_id=post_id)

            self.send_message(message['user_id'], "Пост с ID%s удален из очереди." % post_id)
            print "[INFO] Post ID%s removed from schedule" % post_id
        else:
            self.send_message(message['user_id'], "Пост с ID%s не найден или уже опубликован." % post_id)

    def delayed_publish(self, message):
        if ' ' not in message['body']:
            self.send_message(message['user_id'], "Команда delayed_publish требует как минимум 2 аргумента.\n"
                                                  "delayed_publish время_публикации количество_лайков текст_сообщения")
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
            self.send_message(message['user_id'], "Время до публикации отложенной записи указано не верно. "
                                                  "Формат: ЧЧ:ММ Максимальное время отложенной публикации: 99:59")

    def publish(self, message, delay=0):
        if ' ' in message['body']:
            likes, message_text = message['body'].encode('utf-8').split(' ', 1)
        else:
            likes, message_text = message['body'], ''

        try:
            likes = int(likes)
        except ValueError:
            likes = 0

        attachments = [(attachment['type'], attachment[attachment['type']]) for attachment in message['attachments']] if 'attachments' in message.keys() else []

        if sum([1 if x[0] == 'video' else 0 for x in attachments]) == 0:
            self.send_message(message['user_id'], "Вы забыли прикрепить видео.")
            return

        self._db.insert("posts", likes=likes, message=message_text.decode('utf-8'), author=message['user_id'],
                        published=False, got_likes=False, publish_at=int(time()) / 60 + delay)

        post_id = self._db.get_last_id("posts")
        print "[INFO] New post created: ID%s" % post_id

        for attachment_type, attachment in attachments:
            result = self._db.select("attachments", type=attachment_type,
                                     src_owner_id=attachment['owner_id'], src_document_id=attachment['id'])
            if len(result) == 0:
                owner_id, document_id = attachment['owner_id'], attachment['id']

                if attachment_type == 'doc':
                    request = {
                        'owner_id': attachment['owner_id'],
                        'doc_id': attachment['id']
                    }
                    request.update({'access_key': attachment['access_key']} if 'access_key' in attachment.keys() else {})

                    response = self._api.call("docs.add", **request)
                    owner_id, document_id = self._user_id, response
                elif attachment_type == 'photo':
                    request = {
                        'owner_id': attachment['owner_id'],
                        'photo_id': attachment['id']
                    }
                    request.update({'access_key': attachment['access_key']} if 'access_key' in attachment.keys() else {})

                    response = self._api.call("photos.copy", **request)
                    owner_id, document_id = self._user_id, response

                self._db.insert("attachments", src_owner_id=attachment['owner_id'], src_document_id=attachment['id'],
                                type=attachment_type, owner_id=owner_id, document_id=document_id)
                self._db.insert("post_attachments", post_id=post_id, attachment_id=self._db.get_last_id("attachments"))

                print "[INFO] New attachment[%s] registered: [%s]%s" % (attachment_type, owner_id, document_id)
            else:
                self._db.insert("post_attachments", post_id=post_id, attachment_id=result[0][0])

                print "[INFO] Reused attachment[%s]: [%s]%s" % (attachment_type, result[0][1], result[0][2])

        report = "Задание публикации создано. ID%s" % post_id

        if delay > 0:
            print "[INFO] Post ID%s delayed for %02d:%02d" % (post_id, delay / 60, delay % 60)
            report += " Публикация записи отложена на %02d:%02d" % (delay / 60, delay % 60)

        self.send_message(message['user_id'], report)

    # Bot Methods

    def publish_post_videos(self, post_id):
        for post_attachment in self._db.select("post_attachments", post_id=post_id):
            attachment = self._db.select("attachments", id=post_attachment[2])[0]
            if attachment[3] == "video":
                if attachment[4] == COMMUNITY_ID:
                    self.publish_video(attachment[4], attachment[5])

    def get_post_attachments(self, post_id, include_private=False):
        attachments = []
        for post_attachments in self._db.select("post_attachments", post_id=post_id):
            attachment = self._db.select("attachments", id=post_attachments[2])[0]
            if include_private or not attachment[3] == 'video':
                attachments.append("%s%s_%s" % (attachment[3], attachment[4], attachment[5]))

        return attachments

    def process_message(self, message):
        if message['user_id'] in ADMIN_LIST:
            if ' ' in message['body']:
                cmd, message_body = message['body'].split(' ', 1)
            else:
                cmd, message_body = message['body'], None

            message['body'] = message_body

            if cmd in self._commands.keys():
                self._commands[cmd](message)
            else:
                self.send_message(message['user_id'], "Неизвестная команда. "
                                                      "Посмотреть список команд можно с помощью команды help.")
        else:
            print "[WARN] Message from non-admin user '%s', admin users: %s" % (message['user_id'], ADMIN_LIST)

    def check_posts(self):
        for post in self._db.select("posts"):
            if not post[5] and post[7] <= int(time()) / 60:
                attachments = self.get_post_attachments(post[0], post[2] == 0)

                if post[2] == 0:
                    self.publish_post_videos(post[0])

                post_id = self.publish_post(post[4].encode('utf-8'), attachments=attachments)
                self._db.update("posts", post[0], post_id=post_id, published=True, got_likes=post[2] == 0)
                self.send_message(post[3], "Запись опубликована."
                                           "" + ("" if post[2] == 0 else " Требуемое количество лайков: %d" % post[2]))
                print "[INFO] Post ID%s published. %s likes required." % (post[0], 'No' if post[2] == 0 else post[2])
                sleep(0.2)  # Sleep 200 ms to prevent VK API rate-limit errors
            elif post[5] and not post[6] and post[2] <= self.get_post_likes(post[1]):
                attachments = self.get_post_attachments(post[0], True)
                self.publish_post_videos(post[0])

                self.edit_post(post[1], message=post[4].encode('utf-8'), attachments=attachments)
                self._db.update("posts", post[0], got_likes=True)

                self.send_message(post[3], "Запись собрала требуемое количество лайков. "
                                           "Видео опубликовано.", attachments=self.get_post_attachments(post[0]))
                print "[INFO] Video for post ID%s is published" % post[0]
                sleep(0.2)  # Sleep 200 ms to prevent VK API rate-limit errors

    def run(self):
        try:
            while True:
                self.get_messages()
                self.check_posts()
                sleep(10)
        except KeyboardInterrupt:
            print "[INFO] Shutting down bot..."
        finally:
            self._db.close()


if __name__ == "__main__":
    bot = BotCore()

    bot.run()
