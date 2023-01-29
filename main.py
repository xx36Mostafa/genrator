
        await confirm_button.click()

        # Going to Hypesquad Page
        hypesquad_button = self.page.locator('[aria-controls="hypesquad-online-tab"]')
        await hypesquad_button.click()

        await self.page.wait_for_timeout(random.randint(5000, 6000))

        # Setting Hypesquad
        # payload = {"house_id": random.randint(1, 3)}
        # headers = await Discord.get_headers(self, payload)
        # hypesquad = await self.page.request.post("https://discord.com/api/v9/hypesquad/online", data=payload, headers=headers)
        # print(await hypesquad.json())

        is_locked = await Discord.is_locked(self)
        if is_locked:
            self.logger.error(f"Token {self.token} got locked whilst humanizing!")
            await self.close()
            return

        self.log_output()
        self.logger.info(f"Set Bio and ProfilePic!")

    async def join_server(self):
        await self.page.goto("https://discord.com/channels/@me")
        await self.page.wait_for_timeout(1000)
        # Clicking Join Server Button
        create_join_button = self.page.locator('[data-list-item-id *= "create-join-button"]')
        await create_join_button.click()
        await self.page.wait_for_timeout(500)
        # Clicking Join a Server Button
        another_server_button = self.page.locator('[class *= "footerButton-24QPis"]')
        await another_server_button.click()
        # Type Invite Code
        await self.page.wait_for_timeout(1000)
        await self.page.type("[placeholder='https://discord.gg/hTKzmak']", self.invite_link)
        # Clicking Join Server Button
        join_server_button = self.page.locator('[class *= "lookFilled-yCfaCM"]').last
        await join_server_button.click()

        try:
            await self.page.solve_hcaptcha()
        except:
            self.logger.info("No JoinServer Captcha detected.")

        is_locked = await Discord.is_locked(self)
        if is_locked:
            self.logger.error(f"Token {self.token} got locked whilst joining a Server!")
            await self.close()
            return

        self.log_output()
        self.logger.info("Joined Server successfully.")

    async def is_locked(self):
        token_check = await self.page.request.get('https://discord.com/api/v9/users/@me/library', headers={"Authorization": self.token})
        token_check = token_check.status == 200
        if token_check:
            r = await self.page.request.get('https://discord.com/api/v9/users/@me', headers={"Authorization": self.token})
            response = await r.json()
            self.id = response.get("id")
            self.email = response.get("email")
            self.username = response.get("username")
            self.discriminator = response.get("discriminator")
            self.tag = f"{self.username}#{self.discriminator}"
            self.flags = response.get("public_flags")

        return not token_check

    async def set_email(self, email):
        try:
            # Setting Email
            await self.page.goto("https://discord.com/channels/@me")
            await self.page.wait_for_timeout(1000)
            # Clicking Settings Button
            settings_button = self.page.locator('[class *= "button-12Fmur"]').last
            await settings_button.click()
            # Click Email Button
            await self.page.wait_for_timeout(500)
            settings_button = self.page.locator('[class *= "fieldButton-14lHvK"]').nth(1)
            await settings_button.click()

            # Typing Mail
            mail_input = self.page.locator('[type="text"]').last
            await mail_input.type(email)

            # Typing Password
            password_input = self.page.locator('[type="password"]').last
            await password_input.type(self.browser.faker.password)

            # Click Claim Button
            claim_button = self.page.locator('[type="submit"]').last
            await claim_button.click()
        except Exception as e:
            print(e)

    async def confirm_email(self):
        before_token = self.token
        self.logger.info("Confirming Email...")
        # Getting the email confirmation link from the email
        self.scrape_emails = True
        while self.scrape_emails:
            emails = 'ah'
            for mail in emails:
                if "mail.discord.com" in str(mail.sender):
                    for word in mail.body.split():
                        if "https://click.discord.com" in word:
                            self.email_link = word
                            self.scrape_emails = False
                            break
        self.email_link = self.email_link.replace("[", "").replace("]", "")

        self.logger.info("Waiting 10 seconds for a more realistic email-verify")
        await self.page.wait_for_timeout(random.randint(10000, 12000))

        # Confirming the email by link
        await self.page.goto(self.email_link)

        try:
            await self.page.solve_hcaptcha()
        except:
            self.logger.info("No EmailCaptcha detected")

        # Waiting until new token is set
        while self.token == before_token:
            await self.page.wait_for_timeout(1000)

        is_locked = await Discord.is_locked(self)
        if is_locked:
            self.logger.error(f"Token {self.token} got locked whilst verifying the Email!")
            await self.close()
            return

        self.log_output()
        return True

class Generator:
    async def initialize(self, botright_client,pyt,proxy, mode=None, output_file="output.txt", email=True, humanize=True, output_format="token:email:pass", invite_link=""):
        
        # Initializing the Thread

        self.output_file, self.output_format = output_file, output_format
        self.email_verification, self.humanize, self.invite_link = email, humanize, invite_link
        self.token, self.email, self.output = "", "", ""

        # Initializing Browser and Page
        self.browser = await botright_client.new_browser(proxy)

        self.page = await self.browser.new_page()

        if mode == 1:
            await self.generate_unclaimed(pyt)
        elif mode == 2:
            await self.generate_token(email,pyt)
        elif mode == 3:
            await self.create_invite()
        return

    # Helper Functions
    async def log_token(self):
        async def check_json(route, request):
            await route.continue_()
            try:
                response = await request.response()
                await response.finished()
                json = await response.json()
                if json.get("token"):
                    self.token = json.get("token")
            except Exception:
                pass

        await self.page.route("https://discord.com/api/**", check_json)

    def log_output(self):
        output = ""
        for item in self.output_format.split(":"):
            if "token" in item and self.token:
                output += self.token + ":"
            if "email" in item and self.email:
                output += self.email + ":"
            if "pass" in item:
                output += self.browser.faker.password + ":"
            if "proxy" in item and self.browser.proxy:
                output += self.browser.proxy + ":"

        # Remove last :
        output = output[:-1]
        self.output = output

    async def close(self):
        try:
            await self.page.close()
        except:
            pass
        try:
            await self.browser.close()
        except:
            pass

    async def create_invite(self):
        usernames = get_random_line_and_numbers()
        try:
            await self.page.goto("https://discord.gg/75yccECw")
        except:
            self.logger.error("Site didn´t load")
            await self.close()
        await self.log_token()
        await self.page.type('[class *= "inputDefault-Ciwd-S input-3O04eu"]', usernames)
        await self.page.click('[type *= "submit"]')
        try:
            await self.page.type('[id="react-select-2-input"]', self.browser.faker.birth_day)
        except:
            pass 
        try:
            await self.page.type('[id="react-select-2-input"]', self.browser.faker.birth_day)
            await self.page.keyboard.press("Enter")
            await self.page.type('[id="react-select-3-input"]', self.browser.faker.birth_month)
            await self.page.keyboard.press("Enter")
            await self.page.type('[id="react-select-4-input"]', self.browser.faker.birth_year)
        except:
            pass
        self.logger.info(
                "Successfully Generated Account! Closing Browser...")
    # Main Functions
    async def generate_unclaimed(self,pyt):
        try:
            # Going on Discord Register Site
            try:
                await self.page.goto("https://discord.com/")
            except:
                self.logger.error("Site didn´t load")
                await self.close()
                return False
            # Setting Up TokenLog
            await self.log_token()
            # Click Open InBrowser Button
            await self.page.click('[class *= "gtm-click-class-open-button"]')
            # Typing Username
            await self.page.type('[class *= "username"]', self.browser.faker.username)

            # Clicking Tos and Submit Button
            try:
                await self.page.click("[class *= 'checkbox']", timeout=10000)
            except Exception as e:
                pass
            await self.page.click('[class *= "gtm-click-class-register-button"]')
            try:
                await self.page.click("[class *= 'checkbox']", timeout=20000)
            except:
                pass

            while not self.token:
                await self.page.wait_for_timeout(2000)

            print(f"Generated Token: {self.token}")
            await self.page.wait_for_timeout(2000)

            is_locked = await Discord.is_locked(self)
            if is_locked:
                print(f"Token {self.token} is locked!")
                await self.close()
                return
            else:
                print(f"Token: {self.token} is unlocked! Flags: {self.flags}")

            self.log_output()

            await self.page.wait_for_timeout(3000)
            try:
                await self.page.type('[id="react-select-2-input"]', self.browser.faker.birth_day)
                await self.page.keyboard.press("Enter")
                await self.page.type('[id="react-select-3-input"]', self.browser.faker.birth_month)
                await self.page.keyboard.press("Enter")
                await self.page.type('[id="react-select-4-input"]', self.browser.faker.birth_year)
                await self.page.keyboard.press("Enter")
                await self.page.wait_for_timeout(1000)
                await self.page.keyboard.press("Enter")
            except:
                pass

            # Closing PopUps
            for _ in range(2):
                try:
                    await self.page.click("[class *= 'closeButton']", timeout=5000)
                except:
                    pass

            self.log_output()
            with open(self.output_file, 'a') as file:
                file.write(f"{self.output}\n")


            await self.close()
        # Catch Exceptions and save output anyways
        except:
            if self.output:
                with open(self.output_file, 'a') as file:
                    file.write(f"{self.output}\n")

    async def generate_token(self,em,pyt):
        if em:
            try:
                try:
                    await self.page.goto("https://id.rambler.ru/login-20/mail-registration")
                except:
                    print("Site didn´t load")
                    await self.close()
                usernames = get_random_line_and_numbers()
                self.email = usernames+'@rambler.ru'
                await self.page.type('[id="login"]', usernames)
                await self.page.type('[type="password"]', 'Mobodaa2@@')
                await self.page.type('[id="confirmPassword"]', 'Mobodaa2@@')
                await self.page.solve_hcaptcha()
                input('')
            except:
                pass
        else:
            try:
                ttime=time.time()
                try:
                    await self.page.goto("https://discord.com/register")
                except:
                    self.logger.error("Site didn´t load")
                    await self.close()
                    return False
                # Setting Up TokenLog
                await self.log_token()
                # Typing Email, Username, Password
                d = []
                
                with open(pyt,'r') as filee:
                    emailss = filee.read().splitlines()
                    for i in emailss:
                        d.append(i)
                with open(pyt,'w') as filee:
                    for em in range(len(d)):
                        if em == 0:
                            pass
                        else:
                            filee.write(d[em]+'\n')

                self.email = d[0]
                usernames = get_random_line_and_numbers()
                await self.page.type('[name="email"]', self.email)
                await self.page.type('[name="username"]', usernames)
                await self.page.type('[name="password"]', 'mobodaa2@')

                # Typing BirthDay, BirthMonth, BirthYear
                await self.page.type('[id="react-select-2-input"]', self.browser.faker.birth_day)
                await self.page.keyboard.press("Enter")
                await self.page.type('[id="react-select-3-input"]', self.browser.faker.birth_month)
                await self.page.keyboard.press("Enter")
                await self.page.type('[id="react-select-4-input"]', self.browser.faker.birth_year)
                # Clicking Tos and Submit Button
                try:
                    tos_box = self.page.locator("[type='checkbox']").first
                    await tos_box.click()
                except Exception as e:
                    pass
                await self.page.click('[type="submit"]')

                try:
                    await self.page.click('[type="submit"]')
                    while not self.token:
                        await self.page.wait_for_timeout(2000)
                except:
                    try:
                        while not self.token:
                            await self.page.wait_for_timeout(2000)
                    except:
                        pass
                print(f"Generated Token: {self.token}")
                await self.page.wait_for_timeout(2000)
                is_locked = await Discord.is_locked(self)
                if is_locked:
                    try:
                        await self.page.wait_for_timeout(500)
                        await self.page.click('[class *= "marginBottom20-315RVT button-f2h6uQ lookFilled-yCfaCM colorBrand-I6CyqQ sizeMedium-2bFIHr grow-2sR_-F"]')
                        print(
                        f"Token: {self.token} is unlocked!")
                        with open(self.output_file,'a+') as wr:
                            wr.write(self.token+'==> Test '+'\n')
                    except:
                        print(f"Token {self.token} is locked!")
                        await self.close()
                else:
                    print(
                        f"Token: {self.token} is unlocked! ")

                self.log_output()

                await self.page.wait_for_timeout(2000)

                # Closing PopUps
                for _ in range(2):
                    try:
                        await self.page.click("[class *= 'closeButton']", timeout=5000)
                    except:
                        pass

                await self.page.wait_for_timeout(2000)

                self.log_output()
                with open(self.output_file, 'a') as file:
                    file.write(f"{self.output}\n")
                print("Successfully Generated Account!")
                await self.close()

            # Catch Exceptions and save output anyways
            except:
                if self.output:
                    with open(self.output_file, 'a') as file:
                        file.write(f"{self.output}\n")


async def main():
    botright_client = await botright.Botright(headless=False)
    print('''
████████╗ ██████╗ ██╗  ██╗███████╗███╗   ██╗     ██████╗ ███████╗███╗   ██╗
╚══██╔══╝██╔═══██╗██║ ██╔╝██╔════╝████╗  ██║    ██╔════╝ ██╔════╝████╗  ██║
   ██║   ██║   ██║█████╔╝ █████╗  ██╔██╗ ██║    ██║  ███╗█████╗  ██╔██╗ ██║
   ██║   ██║   ██║██╔═██╗ ██╔══╝  ██║╚██╗██║    ██║   ██║██╔══╝  ██║╚██╗██║
   ██║   ╚██████╔╝██║  ██╗███████╗██║ ╚████║    ╚██████╔╝███████╗██║ ╚████║
   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝     ╚═════╝ ╚══════╝╚═╝  ╚═══╝
''')

    mode = input(" <!... Select For Menu ....!>\n" + "1- Generate Unclaimed Token\n" + "2- Generate Token\n" + "3- Token With Invite\n" + "")
    if mode not in ("1", "2", "3","4"):
        raise ValueError("Invalid Mode provided")
    else:
        mode = int(mode)

    email = False

    humanize = False

    threads = 1
    try:
        threads = int(threads)
    except:
        raise ValueError("Invalid ThreadAmount provided")

    proxies = None

    output_file = input('Enter Output FiLe Path: ')

    if mode in ("1","3"):
        invite_link = input('Enter Invite Link : ')
    else:
        invite_link= "https://discord.gg/scAMnxYcmx"

    output_format = "token:email:pass"
    pyt = input('Enter The Path For Mails: ')
    
    os.system('cls' if os.name == 'nt' else 'clear')
    print('''
████████╗ ██████╗ ██╗  ██╗███████╗███╗   ██╗     ██████╗ ███████╗███╗   ██╗
╚══██╔══╝██╔═══██╗██║ ██╔╝██╔════╝████╗  ██║    ██╔════╝ ██╔════╝████╗  ██║
   ██║   ██║   ██║█████╔╝ █████╗  ██╔██╗ ██║    ██║  ███╗█████╗  ██╔██╗ ██║
   ██║   ██║   ██║██╔═██╗ ██╔══╝  ██║╚██╗██║    ██║   ██║██╔══╝  ██║╚██╗██║
   ██║   ╚██████╔╝██║  ██╗███████╗██║ ╚████║    ╚██████╔╝███████╗██║ ╚████║
   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝     ╚═════╝ ╚══════╝╚═╝  ╚═══╝
''')
    try:
        while True:
            threadz = []
            for _ in range(threads):
                proxy = random.choice(proxies) if proxies else None
                threadz.append(Generator().initialize(botright_client, pyt,proxy, mode, output_file, email, humanize, output_format, invite_link))

            await asyncio.gather(*threadz)
    except KeyboardInterrupt:
        await botright_client.close()
    except Exception:
        await botright_client.close()


asyncio.run(main())
