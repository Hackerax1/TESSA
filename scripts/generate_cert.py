"""
Script to generate self-signed SSL certificates for development or internal use.
For production, use Let's Encrypt or a commercial certificate provider.
"""
from OpenSSL import crypto
import os
from datetime import datetime, timedelta

def generate_self_signed_cert(cert_dir='certs'):
    # Create certificates directory if it doesn't exist
    if not os.path.exists(cert_dir):
        os.makedirs(cert_dir)
    
    # Generate key
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 2048)
    
    # Generate certificate
    cert = crypto.X509()
    cert.get_subject().CN = "proxmox-nli"
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(365*24*60*60)  # Valid for one year
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(key)
    cert.sign(key, 'sha256')
    
    # Save certificate and private key
    cert_path = os.path.join(cert_dir, 'certificate.crt')
    key_path = os.path.join(cert_dir, 'private.key')
    
    with open(cert_path, "wb") as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    
    with open(key_path, "wb") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))
    
    print(f"Generated SSL certificate: {cert_path}")
    print(f"Generated private key: {key_path}")
    return cert_path, key_path

if __name__ == "__main__":
    generate_self_signed_cert()