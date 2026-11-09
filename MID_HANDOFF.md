# ملف التسليم للمحادثة الجديدة — مشروع الميد (Robot Bird)

> **الصق هذا الملف كامل في أول رسالة بالمحادثة الجديدة.**
> وتحته اكتب: "ابدأ معي من المرحلة 1".

---

## 1. مين أنا والوضع

- طالب تصميم ألعاب، مساق **محركات الألعاب**، مبتدئ في البرمجة.
- **التسليم: الثلاثاء الساعة 11 مساءً.** يوم الثلاثاء فيه محاضرة، بشتغل فيها وبعدها في البيت.
- اللعبة: إعادة تصميم Flappy Bird بشكل إبداعي (تصميم جديد + إضافة ميكانيكية إلزامية + شاشة بداية).
- المشرفين **يشوفون المشروع بس** وقت التسليم، ما فيه أسئلة شفهية. بس لو الشغل **واضح إنه AI** (عدم تناسق، جزء متقن جدًا جنب جزء ضعيف) تنزل العلامة.

### القاعدة الوحيدة من المدرس
- ✅ **مسموح:** الذكاء الاصطناعي يكتب الكود، ويعطي أفكار، ويساعد في التصاميم.
- ❌ **ممنوع:** الذكاء الاصطناعي **يشتغل داخل Unity بنفسه** (يركب ويحرك ويضبط).
- **يعني: الكود منك، والتركيب كله بإيدي أنا.**

### اللي صار قبل
أداة AI ركبت أجزاء كثيرة داخل Unity بنفسها، فقررت **أعيد المشروع من الصفر بمشروع جديد**، وأركب كل شي بإيدي. المشروع القديم `miid` يبقى **مرجع أشوفه بس**، وما أنسخ منه ولا مشهد ولا Prefab.

---

## 2. كيف تكلمني (مهم)

- **بالعامية** (خليجي/فلسطيني).
- **خطوة بخطوة:** وين أضغط بالضبط.
- **كل خطوة تحتها سطر "ليش"** عشان أفهم المبدأ وأقدر أعيده.
- ⚠️ **لا تخلط عربي وإنجليزي في نفس السطر** (ينقلب الترتيب ويصير مو مفهوم). أسماء الأزرار والقوائم والقيم بالإنجليزي تكون **في صندوق كود لحالها**، والشرح بالعربي في سطر لحاله.
- **لا تبالغ في الأوقات.** أنا أسرع من اللي تتوقعه.
- بعد كل جزء **أصوّر وأرسل**، وأنت تشيك وبعدين نكمل.
- **وضع الشريك الناقد:** قبل ما توافق حدد افتراض ما انختبر، ابدأ بأقوى حجة ضد، اعتراض واحد كل مرة، استشهد بكلامي، لا مديح ولا مجاملة، نبهني لو أنا متحيز عاطفيًا، واختم بسؤال واحد.
- **لا تفتح أفكار جديدة.** الخطة محسومة تحت. أي فكرة جديدة تنكتب في "بعد التسليم".

---

## 3. البيئة

```
Unity 2022.3.62f3
New Project  >  2D (Core)       (مو Universal 2D ولا 3D)
Built-in Render Pipeline
Input Manager القديم   (Input.GetKeyDown)
rb.velocity            (مو linearVelocity)
Krita للرسم
```
- اسم المشروع الجديد: `RobotBird_Final`
- **اسم ملف السكربت لازم يطابق اسم الـ class.**
- الكاميرا: Orthographic، Size = 5 (تشوف 10 وحدات بالطول، و17.78 بالعرض على 16:9).

---

## 4. هوية اللعبة

- **البطل:** عصفور روبوت Pixel Art، 40×32، **عين ذهبية**، 3 فريمات للجناح (فوق، وسط، تحت) + فريم **طافي** (عين رمادي، جناح نازل).
- **العالم:** مدينة متدمرة. الخلفية من **CraftPix** (مجانية، مجلد `Bright`) مقسومة طبقات.
- **الأنابيب:** ماسورة حديد متدمرة، 32×160 بكسل (1×5 وحدات)، رسمي.
- **العملة:** رسمي.
- **الأعداء:** درون معدني بعين **حمراء**، ومثلث تحذير أحمر يرمش قبل ما يطلع.
- **منطق الألوان:** ذهبي = العصفور والطاقة والفوز. أحمر = خطر وخسارة.

### لوحة الألوان
```
0E0F12   أسود (إطارات)
2A2D33   رمادي معدني غامق
5B5F66   رمادي ظل
8A8F98   لمعة معدن
FFC23D   ذهبي (عين، طاقة، فوز)
FFE58A   ذهبي فاتح (لمعة العين)
FF6A1A   برتقالي (نار، صدأ)
FF2E2E   أحمر (أعداء، خسارة)
```

### الخط
**Pixelify Sans** من Google Fonts. كل نصوص اللعبة فيه.

---

## 5. الشنطة (MID_KIT على سطح المكتب)

**رسوماتي:**
```
Robot Bird.png      Robot Bird 2.png      Robot Bird 3.png
Bird_Off.png        Pipe.png              Coin.png
Enemy.png           Warning.png           Panel.png
```
**الخلفية (CraftPix / Bright):**
```
sky.png   houses&trees_bg.png   houses.png   fence.png   road.png
```
**ما نستخدم:** bird1/2/3، والصورة الكاملة postapocalypse2 (فيها طيور مرسومة)، و car_trees_etc.

**سكربتات المدرس الأصلية** (من الجيميل، مو من المشروع القديم):
```
TubeSpawner.cs   TubeMovement.cs   CoinMovement.cs   BirdJump.cs
```
**وخط** `PixelifySans`.

**Panel.png:** إطار 32×32، حافة 4 بكسل (أسود برا، رمادي `5B5F66`، لمعة `8A8F98` فوق يسار، مسمار بكل زاوية)، والوسط `2A2D33`.

---

## 6. قرارات محسومة

| نسويه | ما نسويه | ليش |
|---|---|---|
| أنبوب عادي 5 وحدات | 9-Slice للأنابيب | ما انذكر بالمادة |
| شاشة سودا بين المشهدين | حفظ مكان الخلفية بين المشهدين | السواد يغطي القفزة |
| ضباب: مربع أبيض نص شفاف **أو** Shader | — | الـShader مسموح ككود، لو أبيه أنسخ ملف الـ`.shader` من المشروع القديم وأسوي الـMaterial بإيدي |
| واجهة بإطار واحد `Panel` (Image Type = Sliced) | واجهة كل عنصر لحاله | التناسق |
| الليزر يطلع من نقطة على العين | ليزر من نص الجسم | كان يبان منفصل |
| الأعداء في مرحلة لحالها (بدون أنابيب) | أعداء مع الأنابيب | كانوا يطلعون من داخل الأنابيب |

---

## 7. تصميم اللعبة (الأرقام)

### إحساس العصفور
```
Rigidbody 2D  >  Gravity Scale  =  2.5
BirdJump      >  Jump Force     =  7.5
```
ليش: قبل كانت 1 و5، فكان بطيء وما يستجيب. الحين كل قفزة ترفعه تقريبًا وحدة.

### الأنابيب (داخل الـPrefab)
```
TubeTop      Position Y = 4.3    Flip Y ✓
TubeBottom   Position Y = -4.3
```
ليش: الفتحة 3.6 (أسهل بالبداية). وأقصى حركة للأنبوب 1 + 0.4 = 1.4 أقل من 1.8 (المسافة قبل ما يبان طرفه).

### TubeManager
```
Position X     =  10
Spawn Rate     =  1.8
Tube Speed     =  3
Height Offset  =  1
```

### المراحل
| الوقت | المرحلة | وش يصير |
|---|---|---|
| 0–5 | استراحة | أول أنبوب جاي |
| 5–20 | تعلّم | أنابيب عادية + عملات |
| 20 | أسرع | سرعة 4، كل 1.5 ثانية، وتسريع الموجودة |
| 35 | تمايل | الأنابيب تتحرك فوق وتحت |
| 47 | هدوء | الأنابيب توقف، آخرها يطلع |
| 50 | السما | تحذير ← درون سريع. الليزر بـF لو العملات 15 أو أكثر |
| 75 | آخر عدو | الأعداء يوقفون |
| 80 | فوز | YOU ESCAPED |

### الطاقة والأعداء
```
BirdJump      >  Laser Cost    =  15
Enemy         >  CoinMovement  >  Move Speed = 7
EnemySpawner  >  Spawn Rate    =  1.8
EnemySpawner  >  Warning Time  =  0.8
EnemySpawner  >  Warning X     =  8
EnemySpawner  >  Position X    =  10
TubeWobble    >  Amount = 0.4   Speed = 2
```

---

## 8. ترتيب الشغل بكرة

| # | المرحلة | تشيك |
|---|---|---|
| 1 | مشروع جديد + مجلدات + الشنطة + إعدادات الصور (PPU، Point، None) | الـConsole فاضي |
| 2 | **الأساس:** TubeManager + Tubes Prefab + العصفور (Animator 4 فريمات، Samples 8) + الواجهة + الحدود | قفز، موت، Retry |
| 3 | العملة داخل الفتحة + الخلفية الطبقات + Parallax + الضباب | العملة تنجمع، الخلفية تلف |
| 4 | GameDirector + الفوز + شريط الطاقة | لوحة الفوز تطلع |
| 5 | التمايل + الأعداء + التحذير + الليزر من العين | F يدمر العدو |
| 6 | الواجهة بإطار Panel + الخط | كل شي متناسق |
| 7 | مشهد Start: عصفور طافي ← START ← يضوي ← سواد ← اللعبة + Build Settings | الانتقال يشتغل |
| 8 | ألعبها كاملة 3 مرات، أرتب الهايراركي والمجلدات، أسلّم | — |

**وقفات ثابتة:**
- **الساعة 8:** لو ما بديت المرحلة 7، شاشة بداية بسيطة (عنوان + START).
- **الساعة 9:30:** أوقف وأسلّم.

**للتجربة السريعة:** أقسم أوقات GameDirector على 4، وأرجعها بعدين.

---

## 9. ملاحظات تركيب مهمة

- **الكانفس:** `Screen Space - Camera`، `Render Camera = Main Camera`، `Order in Layer = 100` (عشان الواجهة فوق الأنابيب).
- **Tags:** `Ground` (أنابيب وحدود)، `Coin`، `Enemy`. حرف كبير بالأول.
- **العملة داخل الفتحة:** ابن لـ`Tubes` في (0,0,0)، **بدون CoinMovement** (الأب يحركها)، `Is Trigger ✓`.
- **الأنبوب بعد تغيير الصورة:** Scale = 1، والكولايدر ⋮ ← Reset.
- **طبقات الخلفية:** Mesh Type = `Full Rect` (عشان العرض ما ينقص)، نسختين لكل طبقة (الثانية X = عرض الصورة). الترتيب:
```
sky -10   houses&trees_bg -9   houses -8   fog -7   fence -6   road -5
سرعات:  0.1   0.3   0.6   —   1.2   3
```
  (الطريق نفس سرعة الأنابيب في البداية عشان تبان مغروسة.)
- **Sprite Color** يغمّق بس (ضرب)، ما يفتّح. للتفتيح: مربع ضباب أو الـShader.
- **LineRenderer** ما يتركب على نفس كائن العصفور (فيه SpriteRenderer). يتركب على ابن اسمه `Laser`. وإعداداته:
```
Width          0.15 → 0.05
Color          FFE58A → FF6A1A
Material       Sprites-Default
Use World Space ✓
Sorting Order  5
```
- **EyePoint:** كائن فاضي ابن للعصفور، محطوط على العين بالضبط.
- **Canvas Group:** Alpha للشكل بس. اللي يمنع الضغط هو `Blocks Raycasts` و`Interactable`.
- **Fader:** صورة سودا تغطي الشاشة، Canvas Group، `Blocks Raycasts ☐`، آخر عنصر بالكانفس.
- **Build Settings:** `0 Start` و`1 Game`.
- **static** ما يرجع لحاله مع Restart، فـGameDirector يصفّره في Start.
- **Loop Time ☐** لأي أنيميشن ما نبيه يعيد.

---

## 10. الأكواد النهائية

### BirdJump.cs (بدل نسخة المدرس)
```csharp
using System.Collections;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;
using TMPro;

public class BirdJump : MonoBehaviour
{
    public float jumpForce = 7.5f;
    private Rigidbody2D rb;
    private bool IsAlive = true;
    public GameObject DeathPanel;
    public TMP_Text CoinDisplay;
    private int score = 0;

    public AudioClip coinSound;
    private AudioSource audioSource;

    [Header("Win")]
    public GameObject WinPanel;

    [Header("Energy & Laser")]
    public Slider energyBar;
    public int laserCost = 15;
    public Transform eyePoint;
    public LineRenderer laserLine;

    private void Awake()
    {
        rb = GetComponent<Rigidbody2D>();
        audioSource = GetComponent<AudioSource>();
        DeathPanel.SetActive(false);

        if (WinPanel != null) WinPanel.SetActive(false);

        if (energyBar != null)
        {
            energyBar.maxValue = laserCost;
            energyBar.value = 0;
        }

        if (laserLine != null) laserLine.enabled = false;
    }

    private void Update()
    {
        if (!IsAlive) return;

        if (Input.GetKeyDown(KeyCode.Space) || Input.GetMouseButtonDown(0))
        {
            Jump();
        }

        if (Input.GetKeyDown(KeyCode.F) && score >= laserCost && laserLine != null)
        {
            StartCoroutine(ShootLaser());
        }
    }

    private void Jump()
    {
        rb.velocity = Vector3.zero;
        rb.AddForce(Vector2.up * jumpForce, ForceMode2D.Impulse);
        transform.rotation = Quaternion.Euler(0f, 0f, 35f);
    }

    private void FixedUpdate()
    {
        if (rb.velocity.y < 0)
        {
            transform.rotation = Quaternion.Lerp(transform.rotation, Quaternion.Euler(0, 0, -45), Time.deltaTime * 2f);
        }
    }

    private void OnCollisionEnter2D(Collision2D collision)
    {
        if (collision.gameObject.CompareTag("Ground") || collision.gameObject.CompareTag("Enemy"))
        {
            Die();
        }
    }

    private void Die()
    {
        IsAlive = false;
        rb.velocity = Vector3.zero;
        rb.isKinematic = true;
        DeathPanel.SetActive(true);
        Time.timeScale = 0f;
    }

    public void Win()
    {
        if (!IsAlive) return;
        IsAlive = false;
        rb.velocity = Vector3.zero;
        rb.isKinematic = true;
        if (WinPanel != null) WinPanel.SetActive(true);
        Time.timeScale = 0f;
    }

    public void RestartGame()
    {
        Time.timeScale = 1f;
        SceneManager.LoadScene(SceneManager.GetActiveScene().buildIndex);
    }

    public void GoToMenu()
    {
        Time.timeScale = 1f;
        SceneManager.LoadScene("Start");
    }

    private void OnTriggerEnter2D(Collider2D collision)
    {
        if (collision.CompareTag("Coin"))
        {
            CollectCoin(collision.gameObject);
        }
    }

    private void CollectCoin(GameObject coin)
    {
        score++;
        CoinDisplay.text = score.ToString();

        if (energyBar != null)
        {
            energyBar.value = Mathf.Min(score, laserCost);
        }

        Destroy(coin);

        if (coinSound != null && audioSource != null)
        {
            audioSource.PlayOneShot(coinSound);
        }
    }

    private IEnumerator ShootLaser()
    {
        Vector3 start = eyePoint != null ? eyePoint.position : transform.position;
        Vector3 end = start + Vector3.right * 20f;

        RaycastHit2D[] hits = Physics2D.RaycastAll(start, Vector2.right, 20f);
        foreach (RaycastHit2D hit in hits)
        {
            if (hit.collider.CompareTag("Enemy"))
            {
                end = hit.point;
                Destroy(hit.collider.gameObject);
                break;
            }
        }

        laserLine.SetPosition(0, start);
        laserLine.SetPosition(1, end);
        laserLine.enabled = true;
        yield return new WaitForSeconds(0.1f);
        laserLine.enabled = false;
    }
}
```

### GameDirector.cs
```csharp
using UnityEngine;

public class GameDirector : MonoBehaviour
{
    public TubeSpawner spawner;
    public BirdJump bird;

    public float fastTime = 20f;
    public float wobbleTime = 35f;
    public float stopPipesTime = 47f;
    public float enemyTime = 50f;
    public float stopEnemiesTime = 75f;
    public float winTime = 80f;

    private float timer = 0f;
    private bool fast, wobble, pipesStopped, enemies, enemiesStopped;

    void Start()
    {
        TubeWobble.active = false;
        EnemySpawner.active = false;
    }

    void Update()
    {
        timer += Time.deltaTime;

        if (!fast && timer >= fastTime)
        {
            fast = true;
            spawner.tubeSpeed = 4f;
            spawner.spawnRate = 1.5f;
            foreach (TubeMovement tube in FindObjectsOfType<TubeMovement>())
            {
                tube.moveSpeed = 4f;
            }
        }

        if (!wobble && timer >= wobbleTime)
        {
            wobble = true;
            TubeWobble.active = true;
        }

        if (!pipesStopped && timer >= stopPipesTime)
        {
            pipesStopped = true;
            spawner.enabled = false;
        }

        if (!enemies && timer >= enemyTime)
        {
            enemies = true;
            EnemySpawner.active = true;
        }

        if (!enemiesStopped && timer >= stopEnemiesTime)
        {
            enemiesStopped = true;
            EnemySpawner.active = false;
        }

        if (timer >= winTime)
        {
            bird.Win();
            enabled = false;
        }
    }
}
```

### TubeWobble.cs (على أب الـPrefab)
```csharp
using UnityEngine;

public class TubeWobble : MonoBehaviour
{
    public static bool active = false;
    public float amount = 0.4f;
    public float speed = 2f;

    private float startY;
    private float t = 0f;

    void Start()
    {
        startY = transform.position.y;
    }

    void Update()
    {
        if (!active) return;

        t += Time.deltaTime;
        Vector3 pos = transform.position;
        pos.y = startY + Mathf.Sin(t * speed) * amount;
        transform.position = pos;
    }
}
```
(العداد `t` يبدأ من صفر لحظة ما يبدأ التمايل، فما ينط الأنبوب فجأة.)

### EnemySpawner.cs
```csharp
using System.Collections;
using UnityEngine;

public class EnemySpawner : MonoBehaviour
{
    public static bool active = false;
    public GameObject enemyPrefab;
    public GameObject warningPrefab;
    public float spawnRate = 1.8f;
    public float warningTime = 0.8f;
    public float warningX = 8f;

    private float timer = 0f;

    void Update()
    {
        if (!active) return;

        timer += Time.deltaTime;
        if (timer >= spawnRate)
        {
            timer = 0f;
            StartCoroutine(SpawnWithWarning());
        }
    }

    private IEnumerator SpawnWithWarning()
    {
        float y = Random.Range(-3.5f, 3.5f);

        GameObject warning = Instantiate(warningPrefab, new Vector3(warningX, y, 0f), Quaternion.identity);
        yield return new WaitForSeconds(warningTime);
        Destroy(warning);

        Instantiate(enemyPrefab, new Vector3(transform.position.x, y, 0f), Quaternion.identity);
    }
}
```

### Blink.cs (على مثلث التحذير، بدون Collider)
```csharp
using UnityEngine;

public class Blink : MonoBehaviour
{
    public float interval = 0.1f;
    private SpriteRenderer sr;
    private float t = 0f;

    void Start()
    {
        sr = GetComponent<SpriteRenderer>();
    }

    void Update()
    {
        t += Time.deltaTime;
        if (t >= interval)
        {
            t = 0f;
            sr.enabled = !sr.enabled;
        }
    }
}
```

### ParallaxLayer.cs (على كل نسخة من كل طبقة)
```csharp
using UnityEngine;

public class ParallaxLayer : MonoBehaviour
{
    public float speed = 1f;
    private float width;

    void Start()
    {
        width = GetComponent<SpriteRenderer>().bounds.size.x;
    }

    void Update()
    {
        transform.position += Vector3.left * speed * Time.deltaTime;

        if (transform.position.x <= -width)
        {
            transform.position += new Vector3(width * 2f, 0f, 0f);
        }
    }
}
```

### StartSequence.cs (مشهد Start، على MenuController)
```csharp
using System.Collections;
using UnityEngine;
using UnityEngine.SceneManagement;

public class StartSequence : MonoBehaviour
{
    public Animator birdAnimator;
    public CanvasGroup fader;
    public string gameScene = "Game";

    private bool started = false;

    public void PressStart()
    {
        if (started) return;
        started = true;
        StartCoroutine(Run());
    }

    private IEnumerator Run()
    {
        birdAnimator.enabled = true;
        yield return new WaitForSeconds(1f);

        float t = 0f;
        while (t < 1f)
        {
            t += Time.deltaTime * 2f;
            fader.alpha = t;
            yield return null;
        }

        SceneManager.LoadScene(gameScene);
    }
}
```
- `StartBird`: صورة `Bird_Off`، Position (-5, 0, 0)، Animator فيه Controller العصفور **ومطفي** (☐).
- `gameScene` لازم يطابق اسم مشهد اللعبة بالضبط.

### FadeIn.cs (مشهد اللعبة، على Fader)
```csharp
using System.Collections;
using UnityEngine;

public class FadeIn : MonoBehaviour
{
    public CanvasGroup fader;

    void Start()
    {
        StartCoroutine(Run());
    }

    private IEnumerator Run()
    {
        fader.alpha = 1f;
        while (fader.alpha > 0f)
        {
            fader.alpha -= Time.deltaTime * 2f;
            yield return null;
        }
    }
}
```

---

## 11. بعد التسليم (أفكار مؤجلة)
- بوس في النهاية.
- أنبوب ثاني بتصميم مختلف يطلع عشوائي.
- أصوات (قفز، موت، فوز، ليزر).
- العنوان يرمش مثل نيون خربان.
