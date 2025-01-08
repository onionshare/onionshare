# You should be able to
### Run existing tests, understanding their purpose and fundamentality.
### Provide results of the existing tests.
### The bugs encountered, what do the tests do, what problems do they solve, how they fulfil requirements, etc.
### Perform exploratory testing on the project.
### Provide details and your methodology, what did you find?
# Your presentation should discuss the following

Mandatory requirements:

### A short description of the project.
Onionshare is a application that lets users securely and anonymously share files, host websites and chat using the tor network. This can be done both trough a downloadable application aswell by using a CLI application written in python, this being the version we focused our work on.

### What is its purpose? What does it aim to accomplish?
 The purpose oif the project is to make secure file sharing and chatting widely available with a limited amount of knowledge in an easy to use enviornment.

### Provide an overview of the requirements and specifications.

The code needs to be able to:

- Connect to the tor network
- **Securely do the following:**
  -  Send messages
  - Send files
  - Revieve files
  - Host websites

### Stakeholders, risks, evaluation, etc.

Main stakeholders are Journalists and Whistleblowers. Their privacy is paramount to be able to do their jobs. This is why applications like these are neccesary.

Secondary stakeholders include the general public. Any individuals who value privacy are bound to try limiting the acces originasations have to their private conversations. This project sets a low acces bar into extreme privacy.

The main risks are the discoveries of new attacks or vulnerabilities that come to light in the software. Since the security is of the utmost importance several audits of the software are conducted irregularly.  
### The past, present, and future development of the project.

#### Past:

- The past development on the github repository cant be seen, all that can be seen is from 2015, which mainly consists of bug fixes and minor changes.
- When Onionshare was audited by Radically Open Security (ROS), the main contributers fixed the security issues and added ways to circumvent censorship.

#### Present:

- The latest change to the github repo is a security update with bug fixes.
- The websites also asks contributers for help with translations for the application, this seems to be a big focus.

#### Future:
While the future as mentioned seems to just consist of security and language updates. There is a lot of functionality that could be created such as image upload in the chat, or voice and video calls.

### The current testing strategy, the kinds of tests being performed, and how the testing is reported on.

The current testing is comprehensive, with pentesting being done by the before mentioned ROS. They also have an array of automated unit tests set up. They also use the Github actions to do continuous integration ensuring code integrity.

### What tools are used? How do they handle bugs?

Bugs are reported in the github issues tab and then assigned to the main developers to fix, by first being reproduced and being given a severity.  

### Document your testing performed.

Our testing focused alot on the already created automated tests
When we were trying to start the application we noticed that the tests
claimed the we didnt have tor installed, even though we did, and that the program would run based on out installation, but not while running the tests.
Thus we remade the test's, to instead of looking for a tor file in a specific folder, we use the code the program uses to start a tor servie, before making a fetch to a tor website to validate that tor is able to start and connect. We could however have seperated these tests. But in order to properly test that tor was functioning, we decided that making a request would be best fitted.

### Exploratory testing is optional, what kind of structured testing will you do?

The Exploratory testing we did included looking at the network traffic to see if the Tor connections was set up properly. When testing this we found the Tor connection was set up correctly even though tests for the correct location for the Tor instalation where failing. Thus we decided to create an automated test that will try to actually connect to the Tor network instead of simulating it in an local enviornment.

### What did you do and what did you find?

We found out by using our newly implemented structured test that the Tor connection gets set up correctly, even when the files aren't necessarily in the right position for the earlier mention tests to pass. We did this by connecting to the tor network the same way the application would and then trying to acces a webadress on the Tor network. after receiving a response we check if it contains the response indicating we a re correctly connected. 

### Document the pre-existing tests and their results.

MENTION ONCE AGAIN THE FAULTY TESTS
MENTION THE WARNINGS FROM TESTS.

