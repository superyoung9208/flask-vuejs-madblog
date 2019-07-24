import time

import sys
from rq import get_current_job

from app import create_app
from app import db
from app.models import User, Message, Task
from app.utils.email import send_email
from config import Config

# RQ worker 在我们的博客Flask应用之外运行，所以需要创建自己的应用实例
app = create_app(config_class=Config)
# 后续会使用Flask-SQLAlchemy来查询数据库，所以需要推送一个上下文使应用成为 "当前" 的应用实例# 后续会使用Flask-SQLAlchemy来查询数据库，所以需要推送一个上下文使应用成为 "当前" 的应用实例
app.app_context().push()


def test_rq(num):
    print('Starting task')
    for i in range(num):
        print(i)
        time.sleep(1)
    print('Task completed')
    return 'Done'


def _set_task_progress(progress):
    job = get_current_job()  # 获取当前后台任务
    if job:
        job.meta['progress'] = progress
        job.save_meta()
        task = Task.query.get(job.get_id())  # 通过id查出task对象
        task.user.add_notification('task_progress', {'task_id': job.get_id(),
                                                     'description': task.description,
                                                     'progress': progress})

        if progress >= 100:  # 进度为100%时，更新Task对象为已完成
            task.complete = True
        db.session.commit()


def send_messages(*args, **kwargs):
    """群发私信"""
    try:
        # 发送者
        _set_task_progress(0)
        i = 0
        sender = User.query.get(kwargs.get('user_id'))
        recipients = User.query.filter(User.id != sender.id)
        total_recipients = recipients.count()

        for user in recipients:
            message = Message()
            message.body = kwargs.get('body')
            message.sender = sender
            message.recipient = user
            db.session.add(message)
            user.add_notification('unread_message_count', user.new_recived_messages())
            db.session.commit()

            # 给接收者发送一封邮件
            text_body = '''
                        Dear {},
                        {}
                        Sincerely,
                        The Madblog Team
                        Note: replies to this email address are not monitored.
                        '''.format(user.username, message.body)

            html_body = '''
                        <p>Dear {0},</p>
                        <p>{1}</p>
                        <p>Sincerely,</p>
                        <p>The Madblog Team</p>
                        <p><small>Note: replies to this email address are not monitored.</small></p>
                        '''.format(user.username, message.body)
            # 后台任务已经是异步了，所以send_email()没必要再用多线程异步，所以这里指定了 sync=True
            send_email('[Madblog] 温馨提醒',
                       sender=app.config['MAIL_SENDER'],
                       recipients=[user.email],
                       text_body=text_body,
                       html_body=html_body,
                       sync=True)

            time.sleep(1)
            i += 1
            _set_task_progress(100 * i // total_recipients)

        job = get_current_job()
        task = Task.query.get(job.get_id())
        task.complate = True
        db.session.commit()

        # 群发结束后，由管理员再给发送方发送一条已完成的提示私信
        message = Message()
        message.body = '[群发私信]已完成, 内容: \n\n' + kwargs.get('body')
        message.sender = User.query.filter_by(email=app.config['ADMINS'][0]).first()
        message.recipient = sender
        db.session.add(message)
        # 给发送方发送新私信通知
        sender.add_notification('unread_messages_count', sender.new_recived_messages())
        db.session.commit()

    except Exception as e:
        app.logger.error('[群发私信]后台任务出错了', exc_info=sys.exc_info())
