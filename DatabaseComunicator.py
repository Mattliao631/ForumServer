import sqlite3
import datetime
import json


class ForumDatabaseCommunicator:
    def __init__(self, database_name):
        self.database_name = database_name
        self.database_connection = sqlite3.connect(self.database_name)
        self.cursor_obj = self.database_connection.cursor()
        self.message = ""
    # Use Case 1
    def CreateUser(self, name, password, mail, time):
        self.cursor_obj.execute(
            '''
                SELECT COUNT(Name)
                FROM User
                WHERE Name == '%s';
            ''' %(name)
        )
        number_of_same_name = (self.cursor_obj.fetchone())[0]
        if number_of_same_name == 0:
            self.cursor_obj.execute("SELECT UserID FROM User ORDER BY UserID DESC;")
            temp_record = self.cursor_obj.fetchone()
            if temp_record is None:
                new_id = 0
            else:
                new_id = temp_record[0] + 1

            
            self.cursor_obj.execute(
                '''
                    INSERT INTO User (UserID, Created_At, Name, Password, Mail, PortraitID)
                    VALUES (%d, '%s', '%s', '%s', '%s', 0);
                ''' %(new_id, time.strftime("%Y/%m/%d, %H:%M:%S"), name, password, mail)
            )
            ###self.database_connection.commit()
            
            self.cursor_obj.execute(
                '''
                    INSERT INTO Pet(MasterID, PetID, Name, Stage, Exp)
                    VALUES (%d, 0, '%s', 0, 0);
                ''' %(new_id, "Pet")
            )
            self.database_connection.commit()
            self.cursor_obj.execute(
                '''
                    INSERT INTO Property(OwneriD, Cookie, Crystal)
                    VALUES (%d, 100, 0);
                ''' %(new_id)
            )
            self.database_connection.commit()
            t = '''{"Message" : "Sign up 0", "Datas" : ""}'''
            self.message = json.dumps(t)
        else:
            t = '''{'Message" : "Sign up 1", "Datas" : ""}'''
            self.message = json.dumps(t)
        
        #print(self.message)
        return self.message

    # Use Case 2
    def SignIn(self, name, password):
        self.cursor_obj.execute(
            '''
                SELECT UserID, Name, Password
                FROM User
                WHERE Name=='%s' AND Password=='%s'
            ''' %(name, password)
        )
        temp = self.cursor_obj.fetchall()
        if not temp:
            t = {"Message" : "Sign in 1", "Datas" : ""}
            self.message = json.dumps(t)
        else:
            id = temp[0][0]
            self.cursor_obj.execute(
                '''
                    SELECT Title, ArticleID, PortraitID
                    FROM Article, User
                    WHERE Article.AuthorID==User.UserID
                    ORDER BY Article.Created_At DESC LIMIT 10;
                '''
            )
            article_temp = self.cursor_obj.fetchall()
            t = {"Message" : "Sign in 0", "Datas" : article_temp}
            self.message = json.dumps(t)

        #print(self.message)
        return self.message
    
    # Use Case 3
    def Search(self, big_category, sub_category, tags):

        query_str = '''
            SELECT DISTINCT Article.Title, User.Name, Article.ArticleID,
            SUM (CASE WHEN Tag.TagName IN (%s) THEN 1 ELSE 0 END) as TagCount
            FROM Article, BigCategory, SubCategory, Categorization, Tag, HasTag, User
            WHERE Article.ArticleID==Categorization.ArticleID AND Article.ArticleID==HasTag.ArticleID
            AND Tag.TagID==HasTag.TagID
            AND BigCategory.CategoryID==Categorization.BigCategoryID AND SubCategory.CategoryID==Categorization.SubCategoryID
            AND BigCategory.CategoryName=='%s' AND SubCategory.CategoryName=='%s'
            GROUP BY Article.ArticleID
            HAVING TagCount > 0
            ORDER BY TagCount DESC, Article.Created_At DESC;
        ''' %(','.join(map(lambda tag: "'"+tag+"'", tags)),big_category, sub_category)

        self.cursor_obj.execute(query_str)
        result_tuples = self.cursor_obj.fetchall()
        
        print(result_tuples)
        
        if not result_tuples:
            t = {"Message" : "Search 1", "Datas" : []}
            self.message = json.dumps(t)
        else:
            t = {"Message" : "Search 0", "Datas" : result_tuples}
            self.message = json.dumps(t)

        #print(self.message)
        return self.message

    # Use Case 8
    def Post(self, Title, Content, Time, AuthorID, BigCategory, SubCategory, Tags):
        # find max articleID
        self.cursor_obj.execute("SELECT MAX(ArticleID) FROM Article;")
        new_id = self.cursor_obj.fetchone()[0] + 1

        # insert article to article table
        query_str = '''
            INSERT INTO Article (ArticleID, Title, Content, Created_At, AuthorID)
            VALUES (%d, '%s', '%s', '%s', %d);
        ''' %(new_id, Title, Content, Time.strftime("%Y/%m/%d, %H:%M:%S"), AuthorID)
        self.cursor_obj.execute(query_str)
        ###self.database_connection.commit()

        # search for matched categoryID with names
        self.cursor_obj.execute('''
            SELECT BigCategory.CategoryID, SubCategory.CategoryID
            FROM BigCategory, SubCategory
            WHERE BigCategory.CategoryName=='%s' AND SubCategory.CategoryName=='%s' AND SubCategory.ParentID==BigCategory.CategoryID
        ''' %(BigCategory, SubCategory)
        )
        id_pair = self.cursor_obj.fetchone()

        # insert category relationship between article and categories
        query_str = '''
            INSERT INTO Categorization (ArticleID, BigCategoryID, SubCategoryID)
            VALUES (%d, %d, %d)
        ''' %(new_id, id_pair[0], id_pair[1])
        self.cursor_obj.execute(query_str)
        ###self.database_connection.commit()

        # find max tagID
        self.cursor_obj.execute("SELECT MAX(TagID) FROM Tag")
        max_tagID = self.cursor_obj.fetchone()[0]

        # find unexist tags
        query_str = '''
            SELECT TagName
            FROM Tag
            WHERE TagName IN (%s)
        ''' %(','.join(map(lambda tag: "'"+tag+"'", Tags)))
        self.cursor_obj.execute(query_str)
        tag_temp = self.cursor_obj.fetchall()
        exist_tags = []
        for elements in tag_temp:
            exist_tags.append(elements[0])
        unexist_tags = list(set(Tags).difference(set(exist_tags)))

        # insert unexist tags
        value_str = ''
        i = max_tagID+1
        for tag in unexist_tags:
            value_str += "(%d, '%s'),\n" %(i, tag)
            i+=1
        value_str = value_str[:-2]
        if value_str:
            query_str = '''
                INSERT INTO Tag (TagID, TagName)
                VALUES
                    %s;
            ''' %(value_str)
            #print(query_str)
            self.cursor_obj.execute(query_str)
        ###self.database_connection.commit()
        # find all matched tag's ID
        self.cursor_obj.execute("SELECT TagID FROM Tag WHERE TagName IN (%s)" %(','.join(map(lambda tag: "'"+tag+"'", Tags))))
        tag_id_temp = self.cursor_obj.fetchall()
        tag_ids = []
        for id in tag_id_temp:
            tag_ids.append(id[0])
        
        # insert tag relationship between article and tag
        query_str = '''
            INSERT INTO HasTag(ArticleID, TagID)
            VALUES
                %s;
        ''' %(',\n'.join(map(lambda tag_id: "(%d," %(new_id) + str(tag_id) + ")", tag_ids)))
        self.cursor_obj.execute(query_str)
        self.database_connection.commit()
    
        t = {"Message" : "Post Article 0", "Datas" : ""}
        self.message = json.dumps(t)
        return self.message
    
    # Use Case 4
    def ViewArticle(self, ArticleID):
        self.cursor_obj.execute('''
                SELECT Article.Title, Article.ArticleID, Article.Content, Article.AuthorID, User.Name
                FROM Article, User
                WHERE Article.ArticleID=='%s' AND Article.AuthorID==User.UserID
            ''' %(ArticleID)
        )
        article_data = list(self.cursor_obj.fetchone())
        #print(article_data)
        self.cursor_obj.execute("SELECT COUNT(UserID) FROM Liked_By WHERE ArticleID==%d" %ArticleID)
        likenum=self.cursor_obj.fetchone()[0]
        article_data.append(likenum)
        #print(article_data)
        bundle_data = [article_data]
        self.cursor_obj.execute(
            '''
                SELECT DISTINCT Comment.CommentID, Comment.Content, Comment.CommenterID, User.Name
                FROM Comment, User
                WHERE Comment.ArticleID==%d AND Comment.CommenterID==User.UserID
                ORDER BY Comment.CommentID;
            ''' %(ArticleID)
        )
        comment_temp = self.cursor_obj.fetchall()
        for comment_tuple in comment_temp:
            bundle_data.append(comment_tuple)

        t = {"Message" : "View Article 0", "Datas" : bundle_data}
        self.message = json.dumps(t)

        return self.message
    
    # Use Case 5
    def Comment(self, ArticleID, UserID, Content, time):
        self.cursor_obj.execute("SELECT COUNT(CommentID) FROM Comment WHERE ArticleID==%d" %(ArticleID))
        new_id = self.cursor_obj.fetchone()[0]
        self.cursor_obj.execute(
            '''
                INSERT INTO Comment (ArticleID, CommentID, Created_At, CommenterID, Content)
                VALUES (%d, %d, '%s', %d, '%s');
            ''' % (ArticleID, new_id, time.strftime("%Y/%m/%d, %H/%M/%S"), UserID, Content)
        )
        self.database_connection.commit()
        t = {"Message" : "Comment 0", "Datas" : ""}
        self.message = json.dumps(t)
        return self.message
    
    # Use Case 6
    def Donate(self, UserID, Amount, AuthorID):
        if UserID!=AuthorID:
            self.cursor_obj.execute("SELECT Cookie FROM Property WHERE OwnerID==%d" %(UserID))
            cookie = self.cursor_obj.fetchone()[0]

            if Amount <= cookie:
                self.cursor_obj.execute(
                    '''
                        UPDATE Property
                        SET Cookie = %d
                        WHERE OwnerID==%d
                    ''' %(cookie - Amount, UserID)
                )
                self.cursor_obj.execute(
                    '''
                        SELECT Pet.MasterID, Pet.PetID, Pet.Stage, Pet.Exp
                        FROM Pet, User
                        WHERE Pet.MasterID==%d AND User.UserID==Pet.MasterID AND User.CurrentPetID==Pet.PetID
                    ''' %(AuthorID)
                )
                pet_temp = self.cursor_obj.fetchone()
                if pet_temp[2] <= 1:
                    if pet_temp[3] + Amount >= Pet_ExpLimit_on_EachStage[pet_temp[2]]:
                        self.cursor_obj.execute(
                            '''
                                UPDATE Pet
                                SET Stage=Stage+1, Exp=Exp-%d
                                WHERE PetID==%d AND MasterID==%d
                            ''' %(Pet_ExpLimit_on_EachStage[pet_temp[2]], pet_temp[1], AuthorID)
                        )
                self.cursor_obj.execute(
                    '''
                        UPDATE Pet
                        SET Exp=Exp+%d
                        WHERE PetID==%d AND Pet.MasterID==%d
                    ''' %(Amount, pet_temp[1], pet_temp[0])
                )
                self.database_connection.commit()
                t = {"Message" : "Donate 0", "Datas" : "%d" %(cookie - Amount)}
                self.message = json.dumps(t)
            else:
                t = {"Message" : "Donate 1", "Datas" : "%d" %(cookie)}
                self.message = json.dumps(t)
            
        else:
            t = {"Message" : "Donate 1", "Datas" : "-1"}
            self.message = json.dumps(t)
        
        #print(self.message)
        return self.message

    #Use Case 7
    def Star(self, UserID ,ArticleID):
        self.cursor_obj.execute("SELECT * FROM Liked_By WHERE ArticleID==%d AND UserID==%d" %(ArticleID, UserID))
        temp = self.cursor_obj.fetchone()
        query_str = ''
        if temp == None:
            query_str = "INSERT INTO Liked_By (ArticleID, UserID) VALUES (%d, %d)" %(ArticleID, UserID)
            t = {"Message" : "Star 0", "Datas" : ""}
            self.message = json.dumps(t)
        else:
            query_str = "DELETE FROM Liked_By WHERE ArticleID==%d AND UserID==%d" %(ArticleID, UserID)
            t = {"Message" : "Star 0", "Datas" : "Unstar"}
            self.message = json.dumps(t)
        
        self.cursor_obj.execute(query_str)
        self.database_connection.commit()
        return self.message

    #Use Case 9
    def ViewUser(self, UserID):
        self.cursor_obj.execute(
            '''
                SELECT User.UserID, User.Name, User.Introduction, User.PortraitID, Pet.PetID, Pet.Name, Pet.Stage, Pet.Exp
                FROM User, Pet
                WHERE UserID==%d AND User.CurrentPetID==Pet.PetID AND Pet.MasterID== User.UserID
            ''' %(UserID)
        )
        temp = self.cursor_obj.fetchone()
        t = {"Message" : "View User 0", "Datas" : temp}
        self.message = json.dumps(t)
        return self.message
    
    #Use Case 10
    def ChangeUserName(self, UserID, NewName):
        self.cursor_obj.execute(
            '''
                UPDATE User
                SET Name='%s'
                WHERE UserID==%d
            ''' %(NewName, UserID)
        )
        self.database_connection.commit()
        t = {"Message" : "Change User Name 0", "Datas" : ""}
        self.message = json.dumps(t)
        return self.message

    #Use Case 11
    def ChangeSelfIntroduction(self, UserID, NewIntroduction):
        self.cursor_obj.execute(
            '''
                UPDATE User
                SET Introduction='%s'
                WHERE UserID==%d
            ''' %(NewIntroduction, UserID)
        )
        self.database_connection.commit()

        t = {"Message" : "Change Self Introduction 0", "Datas" : ""}
        self.message = json.dumps(t)
        return self.message
    
    #Use Case 12
    def ChangePortrait(self, UserID, NewPortraitID):
        self.cursor_obj.execute(
            '''
                UPDATE User
                SET PortraitID=%d
                WHERE UserID==%d
            ''' %(NewPortraitID, UserID)
        )
        self.database_connection.commit()

        t = {"Message" : "Change Portrait 0", "Datas" : ""}
        self.message = json.dumps(t)
        return self.message
    

# Presets
Pet_ExpLimit_on_EachStage = [300, 4000]



if __name__ == "__main__":
    FDC_obj = ForumDatabaseCommunicator("Forum_Database.db")
    #print(FDC_obj.CreateUser(name="T_T", password="Professor Hung is ultimate boss of CSIE", mail="91011112", time=datetime.datetime.now()))
    #print(FDC_obj.SignIn("1234", "4568"))
    #print(FDC_obj.Search(big_category='Test2', sub_category='Test2-0',tags=('Test1', 'Test2')))
    #print(FDC_obj.Post(Title='PythoPosTes', Content='C8763++++++++++++++asdflvnbsdlfkasdfvds;jv asf aa', Time=datetime.datetime.now(), AuthorID=0,BigCategory='Test2', SubCategory='Test2-0', Tags=('Test1', 'Test2', 'RenameTest', 'NewTagTest')))
    #print(FDC_obj.ViewArticle(4))
    #print(FDC_obj.Comment(4, 1, 'ER model', datetime.datetime.now()))
    #print(FDC_obj.Donate(UserID=1, Amount=50, AuthorID=0))
    #print(FDC_obj.Star(UserID=1, ArticleID=3))
    #print(FDC_obj.ViewUser(3))
    #print(FDC_obj.ChangeUserName(3, 'Force us taking complier is nonsense!'))
    #print(FDC_obj.ChangeSelfIntroduction(3, 'Force us taking complier is nonsense!'))
    #print(FDC_obj.ChangePortrait(3, 1))