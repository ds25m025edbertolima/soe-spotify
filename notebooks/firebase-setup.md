PS D:\Documents\00-Personal\01-FHTW\SS2026\MAD-BB-2-SS2026-SOE-Py\soe-spotify> firebase init

     ######## #### ########  ######## ########     ###     ######  ########
     ##        ##  ##     ## ##       ##     ##  ##   ##  ##       ##
     ######    ##  ########  ######   ########  #########  ######  ######
     ##        ##  ##    ##  ##       ##     ## ##     ##       ## ##
     ##       #### ##     ## ######## ########  ##     ##  ######  ########

You're about to initialize a Firebase project in this directory:

  D:\Documents\00-Personal\01-FHTW\SS2026\MAD-BB-2-SS2026-SOE-Py\soe-spotify

✔ Are you ready to proceed? Yes
✔ Which Firebase features do you want to set up for this directory? Press Space to select features, then Enter to confirm your choices. SQL Connect: Set up a Firebase SQL Connect service, Firestore:        
Configure security rules and indexes files for Firestore, Hosting: Set up deployments for static web apps, Storage: Configure a security rules file for Cloud Storage

=== Project Setup

First, let's associate this project directory with a Firebase project.
You can create multiple project aliases by running firebase use --add,

i  Using project fhtw-soe (fhtw-soe) .

=== Dataconnect Setup
i  dataconnect: ensuring required API firebasedataconnect.googleapis.com is enabled...
i  dataconnect: ensuring required API sqladmin.googleapis.com is enabled...
✔ Your project already has existing services. Which would you like to set up local files for? europe-west1/fhtw-soe-service
!  dataconnect: CloudSQL no cost trial has already been used on this project.
!  dataconnect: Cannot detect an existing app in the current directory.
✔ Do you want to create an app template? skip
i  dataconnect\dataconnect.yaml is unchanged
i  dataconnect\example\connector.yaml is unchanged
i  dataconnect: No apps to setup SQL Connect Generated SDKs

=== Firestore Setup
i  firestore: ensuring required API firestore.googleapis.com is enabled...
✔ Please select the location of your Firestore database: europe-west1

Firestore Security Rules allow you to define how and when to allow
requests. You can keep these rules in your project directory
and publish them with firebase deploy.

✔ What file should be used for Firestore Rules? firestore.rules
i  firestore.rules is unchanged

Firestore indexes allow you to perform complex queries while
maintaining performance that scales with the size of the result
set. You can keep index definitions in your project directory
and publish them with firebase deploy.

✔ What file should be used for Firestore indexes? firestore.indexes.json
i  firestore.indexes.json is unchanged

=== Hosting Setup

Your public directory is the folder (relative to your project directory) that
will contain Hosting assets to be uploaded with firebase deploy. If you
have a build process for your assets, use your build's output directory.

✔ What do you want to use as your public directory? public
✔ Configure as a single-page app (rewrite all urls to /index.html)? Yes
✔ Set up automatic builds and deploys with GitHub? Yes

i  Detected a .git folder at D:\Documents\00-Personal\01-FHTW\SS2026\MAD-BB-2-SS2026-SOE-Py\soe-spotify
i  Authorizing with GitHub to upload your service account to a GitHub repository's secrets store.

Visit this URL on this device to log in:
https://github.com/login/oauth/authorize?client_id=89cf50f02ac6aaed3484&state=509366330&redirect_uri=http%3A%2F%2Flocalhost%3A9005&scope=read%3Auser%20repo%20public_repo

Waiting for authentication...

+  Success! Logged into GitHub as ds25m025edbertolima

✔ For which GitHub repository would you like to set up a GitHub workflow? (format: user/repository) ds25m025edbertolima/soe-spotify

+  Created service account github-action-1238738330 with Firebase Hosting admin permissions.
+  Uploaded service account JSON to GitHub as secret FIREBASE_SERVICE_ACCOUNT_FHTW_SOE.
i  You can manage your secrets at https://github.com/ds25m025edbertolima/soe-spotify/settings/secrets.

✔ Set up the workflow to run a build script before every deploy? Yes
✔ What script should be run before every deploy? npm ci && npm run build
✔ GitHub workflow file for PR previews exists. Overwrite? firebase-hosting-pull-request.yml Yes

+  Created workflow file D:\Documents\00-Personal\01-FHTW\SS2026\MAD-BB-2-SS2026-SOE-Py\soe-spotify\.github/workflows/firebase-hosting-pull-request.yml
✔ Set up automatic deployment to your site's live channel when a PR is merged? Yes
✔ What is the name of the GitHub branch associated with your site's live channel? main
✔ The GitHub workflow file for deploying to the live channel already exists. Overwrite? firebase-hosting-merge.yml Yes

+  Created workflow file D:\Documents\00-Personal\01-FHTW\SS2026\MAD-BB-2-SS2026-SOE-Py\soe-spotify\.github/workflows/firebase-hosting-merge.yml

i  Action required: Visit this URL to revoke authorization for the Firebase CLI GitHub OAuth App:
https://github.com/settings/connections/applications/89cf50f02ac6aaed3484
i  Action required: Push any new workflow file(s) to your repo
i  public\index.html is unchanged

=== Storage Setup

Firebase Storage Security Rules allow you to define how and when to allow
uploads and downloads. You can keep these rules in your project directory
and publish them with firebase deploy.

i  storage: ensuring required API firebasestorage.googleapis.com is enabled...
Downloaded the existing Storage Security Rules from the Firebase console
✔ What file should be used for Storage Rules? storage.rules
+  Wrote storage.rules

=== Agent Skills Setup
If you are using an AI coding agent, Firebase Agent Skills make it an expert at Firebase.
✔ Would you like to install agent skills for Firebase? Yes
i  Installing Agent skills in the background...
+  Agent skills installation started

+  Wrote configuration info to firebase.json
+  Wrote project information to .firebaserc

+  Firebase initialization complete!

To get started:

i  Install the SQL Connect VS Code Extensions. You can explore SQL Connect Query on local pgLite and Cloud SQL Postgres Instance.

