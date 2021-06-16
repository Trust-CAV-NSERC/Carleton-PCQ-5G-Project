import base64
import requests
import json
import oqs
import datetime
from Crypto.Cipher import AES
from pprint import pprint
sigalg = "Dilithium5"
kemalg = "Saber-KEM"
server_url = "172.21.30.10"
server_url = "server"
kems = oqs.get_enabled_KEM_mechanisms()
#print("Enabled KEM mechanisms:")
#pprint(kems, compact="True")
sigs = oqs.get_enabled_sig_mechanisms()
#print("Enabled signature mechanisms:")
#pprint(sigs, compact="True")
def login():
    AUTH_SERVER_URL = "http://"+server_url+":5000/auth"
    user = {"username":"user1","password":"user1"}
    token = requests.post(AUTH_SERVER_URL, json = user)
    return token.text

def generateSignerKey():
    with oqs.Signature(sigalg) as signer:
        print (signer.details)
        signer_public_key = signer.generate_keypair()
        secret_key = signer.export_secret_key()
    return base64.b64encode(signer_public_key),base64.b64encode(secret_key)

def generateKEMKeys():
    with oqs.KeyEncapsulation(kemalg) as kem:
        print (kem.details)
        signer_public_key = kem.generate_keypair()
        secret_key = kem.export_secret_key()
    return base64.b64encode(signer_public_key),base64.b64encode(secret_key)
def getProtected(token):
    auth_token = "JWT "+str(token)
    URL = "http://"+server_url+":5000/protected"
    protected = requests.get(URL, headers={"Authorization":auth_token})
    return protected.text

def getPubKey(token):
    auth_token = "JWT "+str(token)
    URL = "http://"+server_url+":5000/server-signer-pubkey"
    protected = requests.get(URL, headers={"Authorization":auth_token})
    return protected.text

def getTestClearTextMessage(token):
    auth_token = "JWT "+str(token)
    URL = "http://"+server_url+":5000/cleartexttestmessage"
    protected = requests.get(URL, headers={"Authorization":auth_token})
    return protected.text

def getCipherText(token,pubkey):
    auth_token = "JWT "+str(token)
    URL = "http://"+server_url+":5000/cipher_text"
    pubKey = {"pubkey":str(pubkey,"utf-8")}
    protected = requests.post(URL, headers={"Authorization":auth_token}, json=pubKey)
    return protected.text

def verifyMessage(message,signature,pubkey):
    now = datetime.datetime.utcnow()
    pubkeyB64_bytes = bytes(pubkey,'utf-8')
    pubkeyB64 = base64.b64decode(pubkeyB64_bytes)
    sigBytes = bytes(signature,'utf-8')
    sigB64 = base64.b64decode(sigBytes)
    with oqs.Signature(sigalg) as verifier:
        # verifier verifies the signature
        message = message.encode()
        is_valid = verifier.verify(message, sigB64, pubkeyB64)
        msg = json.loads(base64.b64decode(message.decode()))
        msg_time = datetime.datetime.utcfromtimestamp(float(msg["time"]))
        diff = now - msg_time
        #print("Valid signature?", is_valid)
        #print("The message is ", msg)
        #print("Now ",str(now))
        #print("Msg time",str(msg_time))
        #print (diff.microseconds/1000)

        return is_valid,diff.microseconds/1000

def testClearTextMessage():
    token = json.loads(login())
    token = token["access_token"]
    pubkey = json.loads(getPubKey(token))["key"]
    testMessage = json.loads(getTestClearTextMessage(token))
    signed_message = testMessage["signed_message"]
    message = testMessage["message"]
    return verifyMessage(message,signed_message,pubkey)

def testCipherText():
    now = datetime.datetime.utcnow()
    keys = kem_keys
    token = json.loads(login())
    token = token["access_token"]
    ciphertext = getCipherText(token,keys[0])
    ciphertext = json.loads(ciphertext)
    client = oqs.KeyEncapsulation(kemalg,base64.b64decode(keys[1]))
    shared_secret_client = client.decap_secret(base64.b64decode(ciphertext["key"]))
    obj = AES.new(shared_secret_client, AES.MODE_ECB)
    msg = obj.decrypt(base64.b64decode(ciphertext["encrypted_message"]))
    decoded_message = base64.b64decode(msg[:-msg[-1]])
    decoded_message = json.loads(decoded_message.decode())
    msg_time = datetime.datetime.utcfromtimestamp(float(decoded_message["time"]))
    diff = now - msg_time
    return diff.microseconds/1000
def test():
    #kemalg = "Kyber1024"
    client_keys = generateKEMKeys()
    server_keys = generateKEMKeys()

    client = oqs.KeyEncapsulation(kemalg,base64.b64decode(client_keys[1]))
    server = oqs.KeyEncapsulation(kemalg,base64.b64decode(server_keys[1]))
    ciphertext, shared_secret_server = server.encap_secret(base64.b64decode(client_keys[0]))
    shared_secret_client = client.decap_secret(ciphertext)
    print("Shared secretes coincide:", shared_secret_client == shared_secret_server)
    #
    #    with oqs.KeyEncapsulation(kemalg) as server:
    #        print("\nKey encapsulation details:")
    #        pprint(client.details)
    #
    #        # client generates its keypair
    #        public_key = client.generate_keypair()
     #       # optionally, the secret key can be obtained by calling export_secret_key()
     #       # and the client can later be re-instantiated with the key pair:
     #       # secret_key = client.export_secret_key()
     #      # store key pair, wait... (session resumption):
      #      # client = oqs.KeyEncapsulation(kemalg, secret_key)

            # the server encapsulates its secret using the client's public key
      #      ciphertext, shared_secret_server = server.encap_secret(public_key)

            # the client decapsulates the the server's ciphertext to obtain the shared secret
    #        shared_secret_client = client.decap_secret(ciphertext)
     #       print (shared_secret_client)
      #      print (shared_secret_server)
       #     print("\nShared secretes coincide:", shared_secret_client == shared_secret_server)
    #obj = AES.new(shared_secret_server, AES.MODE_ECB)
    #message = "The answer is no"
    #ciphertext = obj.encrypt(message)
    #obj2 = AES.new(shared_secret_server, AES.MODE_ECB)
    #msg = obj2.decrypt(ciphertext)
    #print (msg)
def avg(lst):
    return sum(lst) / len(lst)
#test()
signer_keys = generateSignerKey()
kem_keys = generateKEMKeys()
diff_cipher = testCipherText()
valid, diff_clear = testClearTextMessage()

#print ("Cipher Text Message Delay: "+ str(diff_cipher)+"ms. Algorithm "+kemalg)
#print ("Clear Text Message Delay: "+str(diff_clear)+"ms. Algorithm "+sigalg)
diff_cipher_ary = []
diff_ct_ary = []
amount_of_tests = 50
for i in range(0,amount_of_tests):
    diff_cipher = testCipherText()
    valid, diff_clear = testClearTextMessage()
#    valid, diff = testClearTextMessage()
    if valid:
#        #print ("Valid!")
        diff_ct_ary.append(diff_clear)
    diff_cipher_ary.append(diff_cipher)
print ("Average clear text delay over "+str(amount_of_tests)+" tests: "+str(round(avg(diff_ct_ary),3))+"ms")
print ("Average cipher text delay over "+str(amount_of_tests)+" tests: "+str(round(avg(diff_cipher_ary),3))+"ms")
#testAsymTextMessage()