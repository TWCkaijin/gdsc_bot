import discord
from discord.ext import commands
import asyncio
import os 
import numpy as np
import qrcode
import time



class color:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PINK = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    END = '\033[0m'


# 設置intents
intents_ins = discord.Intents.default()
intents_ins.messages = True
intents_ins.members = True
intents_ins.message_content = True
intents_ins.dm_messages = True
bot = commands.Bot(command_prefix="!", intents=intents_ins)
ID_list = {}

def read_key()->str:
    key = ""
    with open(f'{os.getcwd()}/key.txt', 'r') as f:
        key = f.readline()
        f.close()
    return key

def read_mem():
    global server_role_list
    global server_role_mem
    normal_mem = np.genfromtxt(f'{os.getcwd()}/normal.csv', delimiter=',',encoding='utf-8',dtype=str)
    project_mem = np.genfromtxt(f'{os.getcwd()}/project.csv', delimiter=',',encoding='utf-8',dtype=str)
    server_role_mem = [normal_mem,project_mem]
    server_role_list = ["社員","專案組"]

def ID_secured(stu_id, user)->str:
    global ID_list
    if (stu_id in ID_list.values()) and not (user in ID_list.keys()) :
        return "該學號已被使用，請聯繫管理員。"
    elif not (stu_id[0]in['B','M','D'] and len(stu_id)==10):
        print(f'{color.YELLOW}Incorrect ID format{color.END}')
        return "學號格式錯誤，請重新嘗試"
    else:
        return "pass"

def ID_update(user_id,stu_id):
    global ID_list
    ID_list.clear()
    # read the ID_list from the file
    with open(f'{os.getcwd()}/ID_list.txt', 'r') as f:
        for line in f:
            (key, val) = line[0:-1].split(':')
            ID_list[key] = val
        f.close()

    ID_list[user_id] = stu_id
    # write the ID_list to the file
    with open(f'{os.getcwd()}/ID_list.txt', 'w') as f:
        for user, id in ID_list.items():
            f.writelines(f'{user}:{id}\n')
        f.close()




# 機器人啟動
@bot.event
async def on_ready():
    global server_role_list
    global server_role_mem
    print(f'Logged in as {bot.user}')
    server_role_list = []
    server_role_mem = []



#新成員加入
@bot.event
async def on_member_join(member):
    # 獲取伺服器規定頻道
    rules_channel = discord.utils.get(member.guild.channels, name="rules")

    if rules_channel:
        await member.send(f"歡迎加入伺服器！請查閱伺服器規定： {rules_channel.mention}")
    else:
        await member.send("歡迎加入伺服器！請聯繫管理員查閱伺服器規定。")



# 當使用者使用 "!role" 指令時
@bot.command()
async def role(ctx,member: discord.Member=None):
    global server_role_list
    global server_role_mem
    print(f'Verification command received from {ctx.author}')
    user = ctx.message.author
    await user.send(f'請輸入學號以驗證身分：')
    await ctx.message.delete()
    print(f'Sent verification prompt to {user}')
    if member == None:
        member = ctx.author
    current_user_role = member.roles
    print(current_user_role)
    def check(m):
        return m.author == user and isinstance(m.channel, discord.DMChannel)

    try:
        msg = await bot.wait_for('message', check=check, timeout=180.0)
        stu_id = msg.content
        id_check = ID_secured(stu_id ,user)
        if(id_check=="pass"):
            print(f'Received response from {user}: {stu_id}')
            read_mem()
            await role_check(ctx,member ,server_role_list ,current_user_role ,server_role_mem ,stu_id)
            ID_update(user.id,stu_id)
        else:
            await user.send(f"驗證錯誤：{id_check}")
            raise ValueError
        
    except asyncio.TimeoutError:
        await user.send("驗證超時，請重新嘗試。")
        print(f'Verification timeout for {user}')
    
    except ValueError:
        return
    except Exception as e:
        await user.send("驗證錯誤，請重新嘗試或聯絡管理員。")
        print(f'{color.YELLOW}Incorrect verification from {user}{color.END}')
        print(f'{color.RED}Verify Error: {e}{color.END}')



# 當使用者使用 "!sign" 指令時
@bot.command()
async def sign(ctx):
    print(f'Start qenerating sign QRcode for {ctx.message.author}')
    user = ctx.message.author
    await ctx.message.delete()
    text = f"{ID_list[user.id]}" if user.id in ID_list else "No ID"

    if text == "No ID":
        await user.send("請先驗證身分再進行簽到。")
        print(f'{color.YELLOW}No ID found for {user}{color.END}')
        return
    
    img = qrcode.make(text)
    rand_id = np.random.randint(0,10)
    img.save(f"{os.getcwd()}/qrcode{rand_id}.png")
    try:
        msg = await user.send(f'{ID_list[user.id]} 簽到用QRcode，請於60秒內簽到',file=discord.File(f"{os.getcwd()}/qrcode{rand_id}.png"))
        print(f'{color.GREEN}Sign QRcode sent to {user}{color.END}')

        await asyncio.sleep(60)
        await msg.delete()
        os.remove(f"{os.getcwd()}/qrcode{rand_id}.png")
        print(f'{color.GREEN} QRcode removed from {user}{color.END}')
    except Exception as e:
        message = await ctx.send(file=discord.File("qrcode.png"))
        await asyncio.sleep(60)
        await message.delete()



#檢查身分組並分配
async def role_check(ctx ,user:discord.Member ,role_name_list ,user_roles ,role_mem_list ,stu_id):
    for mem_list,role_name in zip(role_mem_list,role_name_list):
        if stu_id in mem_list and not (role_name in [role.name for role in user_roles]):
            role = discord.utils.get(ctx.guild.roles, name=role_name)
            if role:
                await user.add_roles(role)
                await user.send(f'驗證成功，你已獲得 "{role_name}" 身分組！')
                print(f'Assigned {role_name} role to {user}')
            else:
                await user.send(f'未能找到 "{role_name}" 身分組。請聯繫管理員。')
                print(f'{color.RED}Could not find {role_name} role in guild {ctx.guild}{color.END}')
        elif stu_id in mem_list:
            await user.send(f'您先前已獲得 "{role_name}" 身分組。')
    if not any(stu_id in mem_list for mem_list in role_mem_list):
        await user.send(f'您不在 任何 身分組名單中。')
        print(f'{color.YELLOW}No match role for {user}{color.END}')
        return
    print(f'{color.GREEN}Verification finish for{user}{color.END}')



bot.run(read_key())
