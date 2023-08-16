
This set of scripts allows you to set up a personal Juypter Notebook server running on a Google Cloud VM. While
similar in function to Google Cloud Datalab, this approach does not require you to run a gcloud command on your
desktop. Once it is up and running, there is no more desktop code component. The notebook server requires a password you
provide as part of the setup, and also installs a GCP firewall rule to only accept traffic from the IP range you
specify in the setEnvVars.sh file. Note that since Google Compute Engines only support IPV4 traffic, you cannot use IPV6 
with this setup.

1) Edit the `setEnvVars.sh` file to personalize your installation
   -- USER_NAME is the name you would use when ssh-ing into the VM (i.e. jennyg)
   -- the FIREWALL_IP_RANGE address needs to be set to your current IP .. https://whatismyipaddress.com/

2) Run `./startAndLaunch.sh`

3) Browser will (eventually) open to the new VM. Since the certificate is self-signed, you will be required to
   accept the certificate you just created when you first hit the VM.

4) Start a notebook. Note that the system creates five distinct virtualenvs you can choose from to customize your
   environment for each notebook.

5) Alternately, upload a notebook. If you upload an existing notebook, it will select the virtualenv it was
   created with if a matching name exists.

6) The notebook server will start automatically when the VM is started up. CURRENTLY *YOU* must shut the
   VM down when you are done! This can be done using the script `stopVM.sh`.

7) With the VM shut down, you can run the script `restartVM.sh` to bring it back up again.

8) *YOU* are also responsible for deleting the VM, releasing the static IP address, and deleting the firewall rule when you
   retire the VM. For deleting the VM, use the script `deleteVM.sh`. To remove the firewall rule and release the static
   IP address, run `tearDownNetwork.sh`.

9) You can launch your browser to the server anytime using the `run_browser.sh` command (assuming the VM has been started
   using `restartVM.sh`). It pulls the static IP and port you specified from the `setEnvVars.sh` file.
   Be sure to remember your password!

10) The `get_pass.py` script this directory supports the `startAndLaunch.sh` script. It is basically the snippet of code in the
    Jupyter server code base that generates password hashes. The `install_script.sh` is what is uploaded to the VM to
    get the server installed and running.
