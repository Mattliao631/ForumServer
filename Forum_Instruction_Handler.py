from DatabaseComunicator import ForumDatabaseCommunicator
from threading import Lock
import datetime

class ForumInstructionHandler:
    def __init__(self, jmessage):
        self.input = jmessage
        self.command = jmessage['COMMAND']
        self.datas = jmessage['DATAS']
        self.lock = Lock()
        self.FDC_obj = ForumDatabaseCommunicator("Forum_Database.db")

    def handle(self):
        self.lock.acquire()
        
        if self.command == 'Sign up':
            self.output = self.FDC_obj.CreateUser(name=self.datas[0], password=self.datas[1], mail=self.datas[2].replace('@', '%40'), time=datetime.datetime.now())
        elif self.command == 'Sign in':
            self.output = self.FDC_obj.SignIn(name=self.datas[0],password=self.datas[1])
        elif self.command == 'Search':
            self.output = self.FDC_obj.Search(big_category=self.datas[0],sub_category=self.datas[1],tags=self.datas[2])
        elif self.command == 'View Article':
            self.output = self.FDC_obj.ViewArticle(ArticleID = self.datas[0])
        elif self.command == 'Comment':
            self.output = self.FDC_obj.Comment(ArticleID=self.datas[1], UserID=self.datas[0], Content=self.datas[2])
        elif self.command == 'Donate':
            self.output = self.FDC_obj.Donate(UserID=self.datas[0], Amount=self.datas[1], AuthorID=self.datas[2])
        elif self.command == 'Star':
            self.output = self.FDC_obj.Star(UserID=self.datas[0], ArticleID=self.datas[1])
        elif self.command == 'Post Article':
            self.output = self.FDC_obj.Post(Title=self.datas[3],Content=self.datas[4], Time=datetime.datetime.now(), AuthorID=self.datas[0], BigCategory=self.datas[1], SubCategory=self.datas[2], Tags=self.datas[5])
        elif self.command == 'View User':
            self.output = self.FDC_obj.ViewUser(UserID=self.datas[0])
        elif self.command == 'Change User Name':
            self.output = self.FDC_obj.ChangeUserName(UserID=self.datas[0], NewName=self.datas[1])
        elif self.command == 'Change Self Introduction':
            self.output = self.FDC_obj.ChangeSelfIntroduction(UserID=self.datas[0], NewIntroduction=self.datas[1])
        elif self.command == 'change Portrait':
            self.output = self.FDC_obj.ChangePortrait(UserID=self.datas[0], NewPortraitID=self.datas[1])
        else:
            self.output = '''
                {
                    'Message' : 'Unknown instruction',
                    'Dats' : '%s'
                }
            ''' %(self.command)
        
        
        self.lock.release()
        return self.output