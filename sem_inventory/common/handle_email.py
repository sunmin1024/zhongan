import smtplib
import os
import re
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from sem_inventory.common.handleconfig import conf
from sem_inventory.common.handlepath import REPORTDIR


def send_email(filename, title):
    """发送邮件的功能函数"""
    # 第一步：连接邮箱的smtp服务器，并登录
    smtp = smtplib.SMTP_SSL(host=conf.get("email", "host"), port=conf.getint("email", "port"))
    smtp.login(user=conf.get("email", "user"), password=conf.get("email", "pwd"))
    # 第二步：构建邮件
    # 创建一封多组件的邮件
    msg = MIMEMultipart()
    with open(filename, "rb") as f:
        content = f.read()
    # 创建邮件文本内容
    text_msg = MIMEText(content, _subtype="html", _charset="utf8")
    # 添加到多组件的邮件中
    msg.attach(text_msg)
    # 截取附件名称
    res = re.search(r"[1-9]\d*.\d*.\d*.\d*.*", filename)
    add_name = res.group()
    # 创建邮件的附件
    report_file = MIMEApplication(content)
    report_file.add_header('content-disposition', 'attachment', filename=add_name)
    # 将附件添加到多组件的邮件中
    msg.attach(report_file)
    # 主题
    msg["Subject"] = title
    # 发件人
    msg["From"] = conf.get("email", "from_addr")
    # 收件人
    msg["To"] = conf.get("email", "to_addr")

    # 第三步：发送邮箱
    try:
        smtp.send_message(msg, from_addr=conf.get("email", "from_addr"), to_addrs=conf.get("email", "to_addr").split(","))
        print("邮件发送成功")
    except smtplib.SMTPConnectError as e:
        print('邮件发送失败，连接失败:', e.smtp_code, e.smtp_error)
    except smtplib.SMTPAuthenticationError as e:
        print('邮件发送失败，认证错误:', e.smtp_code, e.smtp_error)
    except smtplib.SMTPSenderRefused as e:
        print('邮件发送失败，发件人被拒绝:', e.smtp_code, e.smtp_error)
    except smtplib.SMTPRecipientsRefused as e:
        print('邮件发送失败，收件人被拒绝:', e.smtp_code, e.smtp_error)
    except smtplib.SMTPDataError as e:
        print('邮件发送失败，数据接收拒绝:', e.smtp_code, e.smtp_error)
    except smtplib.SMTPException as e:
        print('邮件发送失败, ', str(e))
    except Exception as e:
        print('邮件发送异常, ', str(e))


if __name__ == '__main__':
    reportdir = os.path.join(REPORTDIR, "2022-08-29_09_00_27reports.html")
    se = send_email(reportdir, "发送邮件测试")
    print(se)
