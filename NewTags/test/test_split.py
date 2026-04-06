url = 'https://nos.netease.com/imglf4/img/050740a531917de3/eE1YZlR4aUVJSU1aV1Ryeks5Wkw5WEx1VlFXVVNMSVhmZEpBTWlSQytkOD0.jpg'
parts = url.split('/')
address = parts[3]
new_url = url.replace(f"https://nos.netease.com/{address}", f"https://{address}.lf127.net")
print(new_url)