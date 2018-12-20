#-*-coding:utf-8-*-
'''
������:AutoCheck_Net_ssh.py
����:zhangrui@xz.chinamobile.com
�Զ�Ѳ�������豸�ű�
����:2018.10.11
    *����ssh��½����
    *�����ж��豸�˿ڣ��Զ�ѡ��telnet����ssh��½��ʽ
    *�Ż�����
    *����ʼ�ǩ��
'''
import paramiko
import telnetlib
import socket
import time
import re
import fileinput
import os
import zipfile
import smtplib  
import sys 
from email.mime.multipart import MIMEMultipart  
from email.mime.text import MIMEText  
from email.mime.application import MIMEApplication

#import pdb
#--------------------------------------------------------
Current_cwd = os.path.abspath(os.path.dirname(__file__))
LogDir = Current_cwd + r'\log'   
LogDirMailToday =LogDir + '\\' + time.strftime('%Y%m%d')#�����ڴ���Ŀ¼
cmdfile_CISCO = Current_cwd + r'\etc\\CMD_Cisco.ini'
cmdfile_HW = Current_cwd + r'\etc\\CMD_HW.ini'
NetworkAddr_FILE = Current_cwd + r'\etc\\Network_Addr.ini'
Password_File =Current_cwd + r'\etc\\password.ini'
SMTP_Sever = 'smtp.139.com'
Mail_List_File = Current_cwd + r'\etc\\Mail_list.ini'
ZipFileDir = LogDirMailToday
ZIPFILE = u'BOSS Network check' + os.path.basename(LogDirMailToday) + '.zip'
os.chdir(Current_cwd)
#---------------------------------------------------------
def Read_Pass():
#��ȡ�豸�˺�����
    f = file(Password_File,'rb')
    content = f.read()
    f.close
    UserName = re.findall("UserName.*=(.*)",content)
    UserName = "".join(UserName).strip()
    PassWord = re.findall("PassWord.*=(.*)",content)
    PassWord = "".join(PassWord).strip()
    SuperPass = re.findall("SuperPass.*=(.*)",content)
    SuperPass = "".join(SuperPass).strip()
    Mail_User = re.findall("Mail_User.*=(.*)",content)
    Mail_User = "".join(Mail_User).strip()
    Mail_Pwd = re.findall("Mail_Pwd.*=(.*)",content)
    Mail_Pwd = "".join(Mail_Pwd).strip()
    return(UserName,PassWord,SuperPass,Mail_User,Mail_Pwd)
'''
Port_check
�˿ڼ�⣺
*.���22��23�˿ڣ�ȷ��ssh/telnet��½��ʽ
*.�˿ڶ����ţ����ݲ��Խ��ѡ���½��ʽ
*.��22��23�˿ڼ��ʧ�ܵ��豸���Ϊfailed
'''
def Port_check(Host,UserName,PassWord):
    failed_count_to = 0
    sc_tcp = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    sc_tcp.settimeout(2)
    port_check_ssh = sc_tcp.connect_ex((Host,22))
    sc_tcp = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    sc_tcp.settimeout(2)
    port_check_telnet = sc_tcp.connect_ex((Host,23))
    if (port_check_ssh == 0 and port_check_telnet == 0):
        try:
            trans = paramiko.Transport((Host, 22))
            trans.start_client()
            trans.auth_password(username=UserName, password=PassWord)
        except Exception,Error_Message:
            Port = 23
        else:
            Port = 22
    elif (port_check_telnet == 0 and port_check_ssh != 0):
        Port = 23
    elif (port_check_ssh == 0 and port_check_telnet != 0):
        Port = 22
    else:
        os.chdir(LogDirMailToday)
        Error_Message = "Time Out"
        Log_Error_File =  Host.strip() + '_failed.txt' 
        log = open(Log_Error_File,'w')
        Error_Log = 'ERROR:' + Host.strip() + ',' + str(Error_Message)
        log.write(Error_Log)
        log.close()
        Port = 'Null'
    #print Host,Port
    return (Port)
'''
AutoCheck_ssh()
ʹ��ssh��½��ʽѲ���豸
*.�˺ŵ�½ʧ�ܵ��豸���Ϊfailed
'''
def AutoCheck_ssh(Host,UserName,PassWord,SuperPass,DeviceName):
    #paramiko.util.log_to_file('paramiko.log')
    content = ""
    success_count_ssh = 0
    failed_count_ssh = 0
    trans = paramiko.Transport((Host, 22))
    try:
        trans.start_client()
        trans.auth_password(username=UserName, password=PassWord)
    except Exception,Error_Message:
        os.chdir(LogDirMailToday)
        Log_Error_File =  Host.strip() + '_failed.txt' 
        log = open(Log_Error_File,'w')
        Error_Log = 'ERROR:' + Host.strip() + ',' + str(Error_Message)
        log.write(Error_Log)
        log.close()
        failed_count_ssh =+ 1   
        trans.close()
    else:    
        channel = trans.open_session()
        channel.get_pty()
        channel.invoke_shell()
        content = []
        #channel.sendall('su' + '\n')
        time.sleep(0.5)
        #channel.sendall(SuperPass + '\n')
        if (DeviceName.find('3750') != -1):
            cmdfile = open(cmdfile_CISCO) 
        else:
            cmdfile = open(cmdfile_HW)
        for cmd in cmdfile:
            #print cmd
            channel.sendall(cmd)
            time.sleep(0.5)
            content.append(channel.recv(9999)) 
        os.chdir(LogDirMailToday)
        LogFile = DeviceName + '.txt'
        log = open(LogFile,'a')
        for log_info in content:
            log.write(log_info)
        success_count_ssh =+ 1       
        channel.close()
        trans.close()     
    return (success_count_ssh,failed_count_ssh)
'''
AutoCheck_telnet()
ʹ��telnet��½��ʽѲ���豸
'''
def AutoCheck_telnet(Host,UserName,PassWord,SuperPass,DeviceName):
    content = ""
    success_count_telnet = 0
    failed_count_telnet = 0
    tn = telnetlib.Telnet(Host.strip(),timeout = 3)
    DeviceType = tn.expect([],timeout=0.5)[2].decode().strip()
    tn.set_debuglevel(2)    
    tn.read_until("Username:",1) 
    tn.write(UserName.encode() + "\n")
    tn.read_until("Password:",1)
    tn.write(PassWord.encode() + "\n")
    tn.write(5*b'\n')
        #pdb.set_trace()
    if (DeviceType.upper().find('Huawei'.upper()) != -1 or DeviceType.upper().find('H3C'.upper()) != -1):#��Ϊ���߻����豸
        cmdfile = file(cmdfile_HW)#�����б�
        DeviceType = 'HW'
        #DeviceFlag = ']'
        tn.write('super'.encode()+ '\n')
        tn.write(SuperPass.encode() + "\n")      
    else:#˼���豸
        cmdfile = file(cmdfile_CISCO)#�����б�
        DeviceType = 'Cisco'
        #DeviceFlag = '#'
        tn.write('enable'.encode()+ '\n')
        tn.write(SuperPass.encode() + "\n")
    for cmd in cmdfile: #�����б������
        tn.write(cmd.strip().encode())
        tn.write(2*b'\n')
        telreply = tn.expect([],timeout=5)[2].decode().strip()#�����־ 
        content = str(content) + str(telreply)
    os.chdir(LogDirMailToday)
    LogFile = DeviceName + '.txt'
    log = open(LogFile,'a')#д����־
    DeviceType = ""
    log.write(content)
    log.close()
    cmdfile.close()   
    success_count_telnet =+ 1            
    return success_count_telnet,failed_count_telnet
'''
Zip_File()
ѹ����־����
'''
def Zip_File(): 
    os.chdir(LogDir)
    LogZip = zipfile.ZipFile(ZIPFILE,'w',zipfile.ZIP_DEFLATED)#ѹ����־
    for filenames in os.walk(ZipFileDir):
        for filename in filenames[-1]:
            LogZip.write(os.path.join(os.path.basename(LogDirMailToday) + '\\' + filename))
            os.remove(LogDirMailToday + '\\' + filename)#ѹ����ɺ�ɾ���ļ����Ա����ɾ��ԭʼĿ¼
    LogZip.close()
    os.removedirs(LogDirMailToday)#ѹ���ɹ���ɾ��ԭʼĿ¼
    return ZIPFILE
'''
Send_Mail()
�����ʼ�����
'''
def Send_Mail(success_count,failed_count,Mail_User,Mail_Pwd):
    Mail_List = file(Mail_List_File)#�ʼ���ַ�б�
    Mail_To   = []
    for list in Mail_List:#��ȡ�ʼ��б��ļ�
        Mail_To.extend(list.strip().split(','))
    Mail_List.close()
    msg = MIMEMultipart() 
    reload(sys)
    sys.setdefaultencoding('utf-8')
    Subject = '�����豸Ѳ��-' + os.path.basename(LogDirMailToday)
    Content = 'Ѳ��ɹ�: ' + str(success_count)  + ' Ѳ��ʧ��: ' + str(failed_count) 
    Content = Content + '<br>' + '<br>' + "-----------" + '<br>' + "����һ���Զ��ʼ����벻Ҫ�ظ�����"
    msg["Subject"] = unicode(Subject) #�ʼ�����
    msg["From"]    = Mail_User  
    msg["To"]      = ",".join(Mail_To)     
    msgContent = MIMEText(Content ,'html','utf-8')  #�ʼ�����
    msgContent["Accept-Language"]="zh-CN"
    msgContent["Accept-Charset"]="ISO-8859-1,utf-8"  
    msg.attach(msgContent)
    attachment = MIMEApplication(open(ZIPFILE,'rb').read()) 
    attachment.add_header('Content-Disposition', 'attachment', filename=os.path.basename(ZIPFILE))  
    msg.attach(attachment)  
    s = smtplib.SMTP_SSL(SMTP_Sever,'465')  
    s.ehlo()  
    s.login(Mail_User, Mail_Pwd)
    s.sendmail(Mail_User, Mail_To, msg.as_string())#�����ʼ�  
    s.close()
def main():
    success_count = 0
    failed_count = 0
    (UserName,PassWord,SuperPass,Mail_User,Mail_Pwd) = Read_Pass()
    if not os.path.exists(LogDirMailToday):
        os.mkdir(LogDirMailToday) 
    for Name_Addr in open(NetworkAddr_FILE):
        success_count_ssh = 0
        success_count_telnet = 0
        failed_count_ssh = 0
        failed_count_telnet = 0
        failed_count_to = 0
        DeviceName = Name_Addr.split(',')[0].strip()
        Host = Name_Addr.split(',')[1].strip()
        (Port) = Port_check(Host,UserName,PassWord)
        if Port == 22:
            (success_count_ssh,failed_count_ssh) = AutoCheck_ssh(Host,UserName,PassWord,SuperPass,DeviceName)
        elif Port == 23:
            (success_count_telnet,failed_count_telnet) = AutoCheck_telnet(Host,UserName,PassWord,SuperPass,DeviceName)
        else:
            failed_count_to =+ 1
        success_count = success_count + success_count_ssh + success_count_telnet
        failed_count = failed_count + failed_count_ssh + failed_count_telnet + failed_count_to
    Zip_File()
    print "success:%s"%success_count
    print "fail:%s"%failed_count
    #Send_Mail(success_count,failed_count,Mail_User,Mail_Pwd)
#--------------------------------------------------------------------------
if __name__ == "__main__":
    main()

