# Leasey Advanced Integration Proposal

**To:** Brian Hartgen, Hartgen Consultancy  
**Subject:** QUILL + Leasey Advanced — a text-editing integration proposal

Dear Brian,

My name is Jeff Bishop. I am the developer of QUILL, an accessible desktop text editor built specifically for screen reader users on Windows. QUILL is a wxPython application designed around the needs of blind and low-vision writers — it prioritises keyboard access, clean speech output, and a workflow that does not get in the way of a screen reader.

I have been an admirer of Leasey Advanced for some time. The text-adjacent features you have built — the category-based notes system, the 12-slot LeaseyClips clipboard, the guided LeaseyWord menu, and the letter-composition workflow — represent a depth of accessibility thinking that is genuinely rare. These are features that work the way a screen reader user actually thinks, not features retrofitted from a sighted workflow.

I am writing because I believe there is a natural and low-friction way for QUILL and Leasey to complement each other, and I would like your blessing before proceeding.

---

## What I would like to build

I am proposing three integrations, all of which are one-directional additions on QUILL's side. None of them require any changes to Leasey or to your code.

### 1. LeaseyNotes editing in QUILL

When Leasey opens a note for editing, it calls Notepad with the note file path. Because notes are stored as plain UTF-8 text files under `C:\LeaseyData\text\`, a QUILL user could register QUILL as their default `.txt` handler and receive those Notepad calls in QUILL instead. QUILL saves the file back as plain text, so Leasey reads it transparently. The entire integration works by virtue of Leasey's own clean file-based design.

### 2. LeaseyClips panel in QUILL

Leasey stores the 12 LeaseyClip slots as plain text files named `JClipOne` through `JClipTwelve`. QUILL could expose these as a named snippet panel — browse the slots, paste one into the current document, or write new content back to a slot — all from within QUILL. Users who work in both applications would have their clips available in either place without any manual copying.

### 3. LeaseyData document browser (opt-in plugin)

QUILL has an extension system. I am considering a plugin that reads your `LeaseyCategories.ini` and `MyDocuments.ini` index files and presents a browseable list of notes and documents. Selecting an item would open it in QUILL for editing and save it back to the same location. No data is moved, duplicated, or reformatted. Leasey's LeaseyCloud sync folder path is respected wherever you have configured it.

---

## What I am not trying to do

I am not trying to replace any Leasey feature, compete with Leasey Advanced, or take users away from Leasey. QUILL is a writing tool; Leasey is a comprehensive productivity layer on top of JAWS. They serve different primary purposes and the overlap is narrow.

I am also not proposing to reverse-engineer or modify any Leasey code. The integrations above are possible entirely because of the clean, file-based design you chose for Leasey's data storage. That design decision is what makes this interoperability practical.

---

## What I am asking for

Primarily, your blessing. I want to make sure you are comfortable with a third-party application interacting with Leasey's data files in the way I have described, and that this does not conflict with anything in your plans for Leasey Advanced.

Beyond that, I would welcome any guidance you are willing to offer — particularly if there are aspects of the data format or expected usage that are not obvious from the outside, or if there are integration approaches you would prefer I avoid.

If at some point you felt that a closer collaboration was worthwhile — for example, noting QUILL as a compatible editor in Leasey's documentation, or coordinating on a more formal integration — I would be very open to that conversation. But I want to be clear that I am not presuming on your time or your product. A straightforward "yes, go ahead" is all I am asking for at this stage.

Thank you for the work you have put into Leasey Advanced over the years. It is one of the more thoughtfully designed pieces of accessibility software I have encountered, and I am grateful it exists.

Warm regards,

Jeff Bishop  
Developer, QUILL  
jeff@jeffbishop.com
