<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0d1117,50:1f6feb,100:f78166&height=220&section=header&text=Prateek%20Kushwaha&fontSize=52&fontColor=ffffff&animation=fadeIn&fontAlignY=36&desc=Software%20Developer%20%E2%80%A2%20Java%20%26%20Spring%20Boot&descSize=20&descAlignY=58" alt="Prateek Kushwaha banner" width="100%" />

<a href="https://git.io/typing-svg">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=22&pause=1200&color=58A6FF&center=true&vCenter=true&width=700&height=40&lines=Software+Developer;Java+%C2%B7+Spring+Boot+%C2%B7+Spring+AI;I+build+backends+and+rebuild+tools+from+scratch" alt="Typing SVG" />
</a>

<br/>

<a href="https://linkedin.com/in/itsprateek4510"><img src="https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn" /></a>
<a href="mailto:prateekkushwaha868@gmail.com"><img src="https://img.shields.io/badge/Email-EA4335?style=for-the-badge&logo=gmail&logoColor=white" alt="Email" /></a>
<img src="https://komarev.com/ghpvc/?username=itsprateek4510&style=for-the-badge&color=1f6feb&label=Profile+views" alt="Profile views" />

</div>

<br/>

## 👋 About me

I'm a software developer from Delhi, studying **B.Tech in Computer Science** at Galgotias College of Engineering & Technology. I like backend work: designing REST APIs, shaping database schemas, and understanding how things work all the way down.

- 🔭 Building a **UPI payment system that works without internet** and a **Git client from scratch**
- ⚙️ Strong on OOP, DSA, microservices, and system design fundamentals
- 🤖 Exploring AI-integrated apps with **Spring AI** and ML
- 🤝 Led the backend on 3+ team projects with Agile sprints, code reviews, and unit tests

<br/>

## 🚧 Featured projects

| Project | What it does | Built with |
| :-- | :-- | :-- |
| **[UPI Offline Mesh Payment System](UPI_REPO_URL)** | Routes UPI payments through a peer-to-peer mesh network when the internet is down. Each transaction is encrypted with hybrid RSA + AES-GCM so relay devices can't read or tamper with it. Every payment settles exactly once, even when several devices upload the same packet at the same time. | Java, Spring Boot |
| **[Git Clone in Python](GITCLONE_REPO_URL)** | A Git client built from scratch with no Git libraries. It talks to remote repos over the Git HTTP protocol, fetches refs, downloads pack files, and parses them to rebuild the commit history, file trees, and working directory. | Python |

### How the offline payment flow works

```mermaid
flowchart LR
    A["Payer device<br/>(no internet)"] -->|"RSA + AES-GCM<br/>encrypted packet"| B["Relay device"]
    B -->|"hop"| C["Relay device<br/>(gets internet)"]
    C -->|"upload"| D["Spring Boot backend"]
    B -->|"upload (duplicate)"| D
    D --> E{"Atomic<br/>deduplication"}
    E -->|"first copy"| F["Settle payment once"]
    E -->|"duplicates"| G["Discard"]
```

<br/>

## 🧰 Tech stack

**Backend**

<img src="https://skillicons.dev/icons?i=java,spring,py" alt="Backend stack" />
<img src="https://img.shields.io/badge/Spring_AI-6DB33F?style=for-the-badge&logo=spring&logoColor=white" alt="Spring AI" />

**Frontend**

<img src="https://skillicons.dev/icons?i=react,js,html,css" alt="Frontend stack" />

**Databases**

<img src="https://skillicons.dev/icons?i=mysql,mongodb" alt="Databases" />

**Tools & Practices**

<img src="https://skillicons.dev/icons?i=git,docker,postman" alt="Tools" />
<img src="https://img.shields.io/badge/REST_APIs-0d1117?style=for-the-badge" alt="REST APIs" />
<img src="https://img.shields.io/badge/WebSocket-0d1117?style=for-the-badge" alt="WebSocket" />
<img src="https://img.shields.io/badge/Agile-0d1117?style=for-the-badge" alt="Agile" />

<br/>

## 📊 GitHub stats

<div align="center">

<img height="170" src="https://github-readme-stats.vercel.app/api?username=itsprateek4510&show_icons=true&theme=tokyonight&hide_border=true&bg_color=0d1117" alt="GitHub stats" />
<img height="170" src="https://github-readme-stats.vercel.app/api/top-langs/?username=itsprateek4510&layout=compact&theme=tokyonight&hide_border=true&bg_color=0d1117" alt="Top languages" />

<img src="https://streak-stats.demolab.com/?user=itsprateek4510&theme=tokyonight&hide_border=true&background=0d1117" alt="Contribution streak" />

</div>

<br/>

## 🧠 How I work

```java
public class Prateek {
    String focus       = "backend systems & system design";
    String curiosity   = "how things work under the hood";
    String[] building  = {"UPI offline mesh payments", "Git, from scratch"};
    boolean testsFirst = true; // APIs, schemas, and unit tests ship together
}
```

<br/>

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:f78166,50:1f6feb,100:0d1117&height=120&section=footer" alt="footer" width="100%" />

</div>
