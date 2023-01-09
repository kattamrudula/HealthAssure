import os
import json
from dotenv import load_dotenv
from web3 import Web3, Account, HTTPProvider
from flask import Flask, render_template, request, current_app as capp
from web3.middleware import geth_poa_middleware
import requests

# load environment variables from .env file
load_dotenv('.env')
# web3.py instance
# w3 = Web3(HTTPProvider(os.environ.get('RPC_URL')))
# print('Web3 Connected:',w3.isConnected())

# account setup
private_key= os.environ.get('PRIVATE_KEY') #private key of the account
public_key = Account.from_key(private_key)
account_address = public_key.address
print(account_address)


today_gas_price_json = requests.get('https://gasstation-mumbai.matic.today/v2').json()
fast_gas_price = today_gas_price_json.get("fast").get('maxPriorityFee')
w3 = Web3(HTTPProvider('https://rpc-mumbai.maticvigil.com/'))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
chain_id = 80001
# Contract instance
abi = json.loads("[{\"inputs\":[],\"stateMutability\":\"nonpayable\",\"type\":\"constructor\"},{\"anonymous\":false,\"inputs\":[{\"indexed\":false,\"internalType\":\"address\",\"name\":\"_from\",\"type\":\"address\"},{\"indexed\":false,\"internalType\":\"uint256\",\"name\":\"_value\",\"type\":\"uint256\"}],\"name\":\"Deposit\",\"type\":\"event\"},{\"anonymous\":false,\"inputs\":[{\"indexed\":false,\"internalType\":\"address\",\"name\":\"_to\",\"type\":\"address\"},{\"indexed\":false,\"internalType\":\"uint256\",\"name\":\"_value\",\"type\":\"uint256\"}],\"name\":\"Withdrawn\",\"type\":\"event\"},{\"inputs\":[],\"name\":\"deposit\",\"outputs\":[{\"internalType\":\"bool\",\"name\":\"\",\"type\":\"bool\"}],\"stateMutability\":\"payable\",\"type\":\"function\"},{\"inputs\":[],\"name\":\"getBalance\",\"outputs\":[{\"internalType\":\"uint256\",\"name\":\"\",\"type\":\"uint256\"}],\"stateMutability\":\"view\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"uint256\",\"name\":\"_amount\",\"type\":\"uint256\"}],\"name\":\"withdraw\",\"outputs\":[{\"internalType\":\"bool\",\"name\":\"\",\"type\":\"bool\"}],\"stateMutability\":\"payable\",\"type\":\"function\"},{\"inputs\":[],\"name\":\"withdrawAllFunds\",\"outputs\":[{\"internalType\":\"bool\",\"name\":\"\",\"type\":\"bool\"}],\"stateMutability\":\"payable\",\"type\":\"function\"}]")
contract_address = ""
payment_medium = w3.eth.contract(abi=abi, address=contract_address)
patients = []
# pylint: disable=C0103
app = Flask(__name__)


@app.route("/")
def index():
    # number = contract_instance.functions.retrieve().call()
    return render_template("Landing.html")

@app.route("/wallet")
def wallet():
    # number = contract_instance.functions.retrieve().call()
    balance_raw = w3.eth.get_balance(contract_address)
    balance = w3.fromWei(balance_raw,'ether')
    return render_template("HospitalWallet.html",balance = balance)

@app.route("/registerPatient", methods=['POST','GET'])
def registerPatient():
    filename = os.path.join(capp.static_folder, 'PatientList.json')
    with open(filename) as patient_file:
        patients = json.load(patient_file)
    if request.method == 'POST':
        name = request.form.get("Name")
        email = request.form.get("Email")
        age = request.form.get("Age")
        gender = request.form.get("Gender")
        reference = request.form.get("Reference")
        treatment = request.form.get("Treatment")
        wallet = request.form.get("Wallet")
        patients.append({"Name":name, "Email":email, "Age":age,"Gender":gender,"Reference":reference,"Treatment":treatment,"Wallet":wallet})
        with open(filename, 'w') as patient_file:
            json.dump(patients, patient_file)
        print(patients)
        return render_template("Patient.html",result="created",patients = patients)
    return render_template("Patient.html",patients = patients)

@app.route("/pay_bill", methods=['POST','GET'])
def pay_bill():
  balance_raw = w3.eth.get_balance(contract_address)
  balance = w3.fromWei(balance_raw,'ether')
  if request.method == 'POST':
    amount_input = request.form.get("amount")
    from_address_input = request.form.get("from_address")
    private_key_input = request.form.get("privatekey")
    # amount = float(amount_input)*10**9
    # print(amount)
    if(not private_key_input.startswith('0x')):
      private_key_input = '0x'+private_key_input
    nonce = w3.eth.get_transaction_count(from_address_input)
    tx_dict = {
        "chainId":chain_id,
        "from":from_address_input,
        "nonce":nonce,
        "value":w3.toWei(amount_input,"ether"),
        "gasPrice":w3.toWei(fast_gas_price,"gwei")
        }
    gas  = w3.eth.estimate_gas(payment_medium.functions.deposit().buildTransaction(tx_dict))
    tx_dict['gas'] = gas
    print(gas)
    payment_transaction = payment_medium.functions.deposit().buildTransaction(tx_dict)
    signed_payment_transaction = w3.eth.account.sign_transaction(payment_transaction, private_key=private_key_input)
    send_payment_transaction = w3.eth.send_raw_transaction(signed_payment_transaction.rawTransaction)
    print(send_payment_transaction.hex())
    tx_reciept = w3.eth.wait_for_transaction_receipt(send_payment_transaction)
    print(tx_reciept)
    if(tx_reciept):
        trans_hash = send_payment_transaction.hex()
    return render_template("PayBill.html", result = trans_hash,wallet_address= contract_address,balance = balance)
  return render_template("PayBill.html",wallet_address= contract_address,balance = balance)

@app.route("/mint_nft", methods=['POST','GET'])
def mint_nft():
    if request.method == 'POST':
        print("entered minting")
        today_gas_price_json = requests.get('https://gasstation-mumbai.matic.today/v2').json()
        fast_gas_price = today_gas_price_json.get("fast").get('maxPriorityFee')
        w3 = Web3(HTTPProvider('https://rpc-mumbai.maticvigil.com/'))
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        chain_id = 80001
        contract_address = "0x7D1D962B81C29DF38eaB88CfD99205f2B90dD071"
        abi = json.loads("[{\"inputs\":[],\"stateMutability\":\"nonpayable\",\"type\":\"constructor\"},{\"anonymous\":false,\"inputs\":[{\"indexed\":true,\"internalType\":\"address\",\"name\":\"owner\",\"type\":\"address\"},{\"indexed\":true,\"internalType\":\"address\",\"name\":\"approved\",\"type\":\"address\"},{\"indexed\":true,\"internalType\":\"uint256\",\"name\":\"tokenId\",\"type\":\"uint256\"}],\"name\":\"Approval\",\"type\":\"event\"},{\"anonymous\":false,\"inputs\":[{\"indexed\":true,\"internalType\":\"address\",\"name\":\"owner\",\"type\":\"address\"},{\"indexed\":true,\"internalType\":\"address\",\"name\":\"operator\",\"type\":\"address\"},{\"indexed\":false,\"internalType\":\"bool\",\"name\":\"approved\",\"type\":\"bool\"}],\"name\":\"ApprovalForAll\",\"type\":\"event\"},{\"inputs\":[{\"internalType\":\"address\",\"name\":\"to\",\"type\":\"address\"},{\"internalType\":\"uint256\",\"name\":\"tokenId\",\"type\":\"uint256\"}],\"name\":\"approve\",\"outputs\":[],\"stateMutability\":\"nonpayable\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"uint256\",\"name\":\"tokenId\",\"type\":\"uint256\"},{\"internalType\":\"uint256\",\"name\":\"price\",\"type\":\"uint256\"}],\"name\":\"createListedToken\",\"outputs\":[],\"stateMutability\":\"payable\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"string\",\"name\":\"tokenURI\",\"type\":\"string\"},{\"internalType\":\"uint256\",\"name\":\"price\",\"type\":\"uint256\"}],\"name\":\"createToken\",\"outputs\":[{\"internalType\":\"uint256\",\"name\":\"\",\"type\":\"uint256\"}],\"stateMutability\":\"payable\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"uint256\",\"name\":\"tokenId\",\"type\":\"uint256\"}],\"name\":\"executeSale\",\"outputs\":[],\"stateMutability\":\"payable\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"address\",\"name\":\"from\",\"type\":\"address\"},{\"internalType\":\"address\",\"name\":\"to\",\"type\":\"address\"},{\"internalType\":\"uint256\",\"name\":\"tokenId\",\"type\":\"uint256\"}],\"name\":\"safeTransferFrom\",\"outputs\":[],\"stateMutability\":\"nonpayable\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"address\",\"name\":\"from\",\"type\":\"address\"},{\"internalType\":\"address\",\"name\":\"to\",\"type\":\"address\"},{\"internalType\":\"uint256\",\"name\":\"tokenId\",\"type\":\"uint256\"},{\"internalType\":\"bytes\",\"name\":\"data\",\"type\":\"bytes\"}],\"name\":\"safeTransferFrom\",\"outputs\":[],\"stateMutability\":\"nonpayable\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"address\",\"name\":\"operator\",\"type\":\"address\"},{\"internalType\":\"bool\",\"name\":\"approved\",\"type\":\"bool\"}],\"name\":\"setApprovalForAll\",\"outputs\":[],\"stateMutability\":\"nonpayable\",\"type\":\"function\"},{\"anonymous\":false,\"inputs\":[{\"indexed\":true,\"internalType\":\"uint256\",\"name\":\"tokenId\",\"type\":\"uint256\"},{\"indexed\":false,\"internalType\":\"address\",\"name\":\"owner\",\"type\":\"address\"},{\"indexed\":false,\"internalType\":\"address\",\"name\":\"seller\",\"type\":\"address\"},{\"indexed\":false,\"internalType\":\"uint256\",\"name\":\"price\",\"type\":\"uint256\"},{\"indexed\":false,\"internalType\":\"bool\",\"name\":\"currentlyListed\",\"type\":\"bool\"}],\"name\":\"TokenListedSuccess\",\"type\":\"event\"},{\"anonymous\":false,\"inputs\":[{\"indexed\":true,\"internalType\":\"address\",\"name\":\"from\",\"type\":\"address\"},{\"indexed\":true,\"internalType\":\"address\",\"name\":\"to\",\"type\":\"address\"},{\"indexed\":true,\"internalType\":\"uint256\",\"name\":\"tokenId\",\"type\":\"uint256\"}],\"name\":\"Transfer\",\"type\":\"event\"},{\"inputs\":[{\"internalType\":\"address\",\"name\":\"from\",\"type\":\"address\"},{\"internalType\":\"address\",\"name\":\"to\",\"type\":\"address\"},{\"internalType\":\"uint256\",\"name\":\"tokenId\",\"type\":\"uint256\"}],\"name\":\"transferFrom\",\"outputs\":[],\"stateMutability\":\"nonpayable\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"uint256\",\"name\":\"_listPrice\",\"type\":\"uint256\"}],\"name\":\"updateListPrice\",\"outputs\":[],\"stateMutability\":\"payable\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"address\",\"name\":\"owner\",\"type\":\"address\"}],\"name\":\"balanceOf\",\"outputs\":[{\"internalType\":\"uint256\",\"name\":\"\",\"type\":\"uint256\"}],\"stateMutability\":\"view\",\"type\":\"function\"},{\"inputs\":[],\"name\":\"getAllNFTs\",\"outputs\":[{\"components\":[{\"internalType\":\"uint256\",\"name\":\"tokenId\",\"type\":\"uint256\"},{\"internalType\":\"address payable\",\"name\":\"owner\",\"type\":\"address\"},{\"internalType\":\"address payable\",\"name\":\"seller\",\"type\":\"address\"},{\"internalType\":\"uint256\",\"name\":\"price\",\"type\":\"uint256\"},{\"internalType\":\"bool\",\"name\":\"currentlyListed\",\"type\":\"bool\"}],\"internalType\":\"struct NFTMarketplace.ListedToken[]\",\"name\":\"\",\"type\":\"tuple[]\"}],\"stateMutability\":\"view\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"uint256\",\"name\":\"tokenId\",\"type\":\"uint256\"}],\"name\":\"getApproved\",\"outputs\":[{\"internalType\":\"address\",\"name\":\"\",\"type\":\"address\"}],\"stateMutability\":\"view\",\"type\":\"function\"},{\"inputs\":[],\"name\":\"getCurrentToken\",\"outputs\":[{\"internalType\":\"uint256\",\"name\":\"\",\"type\":\"uint256\"}],\"stateMutability\":\"view\",\"type\":\"function\"},{\"inputs\":[],\"name\":\"getLatestIdToListedToken\",\"outputs\":[{\"components\":[{\"internalType\":\"uint256\",\"name\":\"tokenId\",\"type\":\"uint256\"},{\"internalType\":\"address payable\",\"name\":\"owner\",\"type\":\"address\"},{\"internalType\":\"address payable\",\"name\":\"seller\",\"type\":\"address\"},{\"internalType\":\"uint256\",\"name\":\"price\",\"type\":\"uint256\"},{\"internalType\":\"bool\",\"name\":\"currentlyListed\",\"type\":\"bool\"}],\"internalType\":\"struct NFTMarketplace.ListedToken\",\"name\":\"\",\"type\":\"tuple\"}],\"stateMutability\":\"view\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"uint256\",\"name\":\"tokenId\",\"type\":\"uint256\"}],\"name\":\"getListedTokenForId\",\"outputs\":[{\"components\":[{\"internalType\":\"uint256\",\"name\":\"tokenId\",\"type\":\"uint256\"},{\"internalType\":\"address payable\",\"name\":\"owner\",\"type\":\"address\"},{\"internalType\":\"address payable\",\"name\":\"seller\",\"type\":\"address\"},{\"internalType\":\"uint256\",\"name\":\"price\",\"type\":\"uint256\"},{\"internalType\":\"bool\",\"name\":\"currentlyListed\",\"type\":\"bool\"}],\"internalType\":\"struct NFTMarketplace.ListedToken\",\"name\":\"\",\"type\":\"tuple\"}],\"stateMutability\":\"view\",\"type\":\"function\"},{\"inputs\":[],\"name\":\"getListPrice\",\"outputs\":[{\"internalType\":\"uint256\",\"name\":\"\",\"type\":\"uint256\"}],\"stateMutability\":\"view\",\"type\":\"function\"},{\"inputs\":[],\"name\":\"getMyNFTs\",\"outputs\":[{\"components\":[{\"internalType\":\"uint256\",\"name\":\"tokenId\",\"type\":\"uint256\"},{\"internalType\":\"address payable\",\"name\":\"owner\",\"type\":\"address\"},{\"internalType\":\"address payable\",\"name\":\"seller\",\"type\":\"address\"},{\"internalType\":\"uint256\",\"name\":\"price\",\"type\":\"uint256\"},{\"internalType\":\"bool\",\"name\":\"currentlyListed\",\"type\":\"bool\"}],\"internalType\":\"struct NFTMarketplace.ListedToken[]\",\"name\":\"\",\"type\":\"tuple[]\"}],\"stateMutability\":\"view\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"address\",\"name\":\"owner\",\"type\":\"address\"},{\"internalType\":\"address\",\"name\":\"operator\",\"type\":\"address\"}],\"name\":\"isApprovedForAll\",\"outputs\":[{\"internalType\":\"bool\",\"name\":\"\",\"type\":\"bool\"}],\"stateMutability\":\"view\",\"type\":\"function\"},{\"inputs\":[],\"name\":\"name\",\"outputs\":[{\"internalType\":\"string\",\"name\":\"\",\"type\":\"string\"}],\"stateMutability\":\"view\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"uint256\",\"name\":\"tokenId\",\"type\":\"uint256\"}],\"name\":\"ownerOf\",\"outputs\":[{\"internalType\":\"address\",\"name\":\"\",\"type\":\"address\"}],\"stateMutability\":\"view\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"bytes4\",\"name\":\"interfaceId\",\"type\":\"bytes4\"}],\"name\":\"supportsInterface\",\"outputs\":[{\"internalType\":\"bool\",\"name\":\"\",\"type\":\"bool\"}],\"stateMutability\":\"view\",\"type\":\"function\"},{\"inputs\":[],\"name\":\"symbol\",\"outputs\":[{\"internalType\":\"string\",\"name\":\"\",\"type\":\"string\"}],\"stateMutability\":\"view\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"uint256\",\"name\":\"tokenId\",\"type\":\"uint256\"}],\"name\":\"tokenURI\",\"outputs\":[{\"internalType\":\"string\",\"name\":\"\",\"type\":\"string\"}],\"stateMutability\":\"view\",\"type\":\"function\"}]")
        nft_medium = w3.eth.contract(address = contract_address, abi = abi)
        amount_input = request.form.get("Price")
        from_address_input = request.form.get("Account")
        private_key_input = request.form.get("PrivateKey")
        token_uri = request.form.get("IPFSUrl")
        print(request.form.get("IPFSUrl"))
        if(not private_key_input.startswith('0x')):
            private_key_input = '0x'+private_key_input
        listing_price = nft_medium.functions.getListPrice().call()
        amount = float(amount_input)
        price = w3.toWei(amount,'ether')
        nonce = w3.eth.get_transaction_count(from_address_input)
        tx_dict = {
            "chainId":chain_id,
            "from":from_address_input,
            "nonce":nonce,
            "value":listing_price,
            "gasPrice":w3.toWei(fast_gas_price,"gwei")
            }
        gas  = w3.eth.estimate_gas(nft_medium.functions.createToken(token_uri, price).buildTransaction(tx_dict))
        tx_dict['gas'] = gas
        print(gas)
        try:
            nft_transaction = nft_medium.functions.createToken(token_uri, price).buildTransaction(tx_dict)
            signed_nft_transaction = w3.eth.account.sign_transaction(nft_transaction, private_key=private_key_input)
            send_nft_transaction = w3.eth.send_raw_transaction(signed_nft_transaction.rawTransaction)
            print(send_nft_transaction.hex())
            tx_reciept = w3.eth.wait_for_transaction_receipt(send_nft_transaction)
            print(tx_reciept)
            if(tx_reciept):
                trans_hash = send_nft_transaction.hex()
                return render_template("MintNFT.html",result = trans_hash)
            return render_template("MintNFT.html",error = "Error!")
        except Exception as ex:
            return render_template("MintNFT.html",error = "Error!")
    return render_template("MintNFT.html")

if __name__ == '__main__':
    server_port = os.environ.get('PORT', '8080')
    app.run(debug=False, port=server_port, host='0.0.0.0')
