# -*- coding: utf-8 -*-
"""
Created on 19.07.2011

@author: Sebastian Wallat
"""

if __name__ == '__main__':
    import dissomniag.auth.User
    dissomniag.auth.User.addUser(username = "admin", password = "b00tloader", publicKey = "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAf0N76ZZlEhL6I3+7bMx2Tje+nuAoJ4ylefaiAvl0w5mnYNIfqw7VUlN4TMjBsBReb8b1mefY5XKBEc2FXKSlCBirQeTap9dfYCMN6fJfQfw2IQFUaiXqUJHyvAqGTTtI5bq8d8QA1Kpuc+VJgGdIQXl5wcn4J+z7zB9BfaCrDsZVDTxbObNqCg8M9mc9mNgcoqHam/F6BuU5EDj1tOqXlWPFr2PgAgvvUAjMwvIbKMZU9IaMdG3hzKdoeYjSlQGhxIXH7Qxmv1MWj/O934eSfRTkYp+HEwmeg4IM/kize6IAfnVh6L4KBq1HKXn8SindeY36SZdSP8cl2H6rnA7w2XfC0ercbi2YjUm5iGAPrODbdd5p1LkTTpBt2dpuM23aBZmaQRcreq420ugipXYAL/THSAQ8mcWPbCoLPj+SDY8+GQLys7Wjzj5N1AlBElY9snbFiDefTsWBHarZEkVvOf3j23UN2pHKUIYteKZTuv0/R1mA2zmQr1Btd/nzUqFZqgLjCXkUZk9iG18wlrPSjkFUQOblGP4dn0kGjj3RZdz8ELr4sCiRiqmfe3RNSnFhqQLYZ+I3EObOKLIcAe2LLILYwln1gQHV2K35O0WpBB9XjPXyl65SWIlKqIUOIRmBRemRoA4M3UCKt1I8FN8HIDgxqlw/LzSIL2SsjkOyw== sw@sw-laptop", isAdmin = True, loginManhole = True, loginSSH = True, loginRPC = True, isHtpasswd = False)
    import dissomniag
    dissomniag.startServer()
