"""
UBC CPE File Naming Tool - Main Application

A Streamlit web app for UBC Continuing Professional Education staff to:
- Generate standardized filenames following CPE conventions
- Navigate file location structure
- Analyze documents with AI for automatic naming suggestions

Modules:
- constants.py: All data models, codes, and configuration
- file_processing.py: File content extraction (PDF, Word, Excel, images)
- filename_generator.py: Filename generation and validation
- file_location.py: File location path generation
- ai_analysis.py: AI analysis (Claude, Gemini, rule-based fallback)
- ui_components.py: Templates, analytics, export, styling
"""

import streamlit as st
import re
from datetime import datetime

from constants import (
    DOCUMENT_FORMS,
    REVISION_STATUSES,
    FILE_EXTENSIONS,
    PARTNERS,
    CPE_INTERNAL_BLOCKS,
    CPE_INTERNAL_SUBCATEGORIES,
    DEFINITION_APPROVALS_BLOCKS,
    PRODUCTION_DELIVERY_BLOCKS,
    HELP_CONTENT,
    FILE_LOCATION_HELP,
    SUPPORTED_FILE_TYPES,
)
from filename_generator import (
    generate_filename,
    validate_all_fields,
    check_filename_length,
)
from file_location import generate_file_location_path
from file_processing import read_file_content, compute_file_hash
from ai_analysis import (
    analyze_with_claude,
    analyze_with_gemini,
    analyze_with_rules,
    get_confidence_level,
)
from ui_components import (
    CUSTOM_CSS,
    ACCESSIBILITY_HTML,
    get_all_templates,
    save_custom_template,
    delete_custom_template,
    init_analytics,
    track_filename_generated,
    track_ai_analysis,
    track_location_generated,
    get_analytics_summary,
    export_results_to_csv,
    save_results,
    get_saved_results,
    clear_saved_results,
)

# ─── Page configuration ───────────────────────────────────────────────────

st.set_page_config(
    page_title="UBC CPE File Naming Tool",
    page_icon="\U0001f4c1",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize analytics
init_analytics(st.session_state)

# Inject CSS and accessibility features
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
st.markdown(ACCESSIBILITY_HTML, unsafe_allow_html=True)

# ─── Authentication ────────────────────────────────────────────────────────

def check_auth() -> bool:
    """Check if authentication is enabled and if user is authenticated."""
    try:
        auth_enabled = st.secrets.get("AUTH_ENABLED", False)
    except Exception:
        return True  # No secrets configured, skip auth

    if not auth_enabled:
        return True

    if st.session_state.get("authenticated"):
        return True

    st.markdown("""
    <div class="main-header">
        <h1>UBC CPE File Naming Tool</h1>
        <p>Please sign in to continue</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        username = st.text_input("Username", autocomplete="username")
        password = st.text_input("Password", type="password", autocomplete="current-password")
        submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)

        if submitted:
            try:
                valid_users = st.secrets.get("USERS", {})
                if username in valid_users and valid_users[username] == password:
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = username
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
            except Exception:
                st.error("Authentication configuration error.")

    return False


if not check_auth():
    st.stop()

# ─── Main App Header ──────────────────────────────────────────────────────

st.markdown("""
<div class="main-header">
    <h1>UBC CPE File Naming Tool <span class="version-badge">V3</span></h1>
    <p style="color: #666;">Generate standardized filenames, find file locations, and analyze files with AI</p>
</div>
""", unsafe_allow_html=True)

# ─── Main Tabs ─────────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4 = st.tabs([
    "\U0001f4dd Manual Generator",
    "\U0001f4c1 File Location",
    "\U0001f916 AI File Analyzer",
    "\U0001f4ca Dashboard",
])


# ==================== MANUAL GENERATOR TAB ====================
with tab1:
    col1, col2 = st.columns([1, 3])

    with col1:
        st.markdown('<div class="help-panel">', unsafe_allow_html=True)
        st.subheader("Field Guide")

        help_topic = st.selectbox(
            "Select a field to learn more:",
            [""] + list(HELP_CONTENT.keys()),
            format_func=lambda x: HELP_CONTENT[x]["title"] if x else "Select a field...",
        )

        if help_topic:
            st.info(
                f"**{HELP_CONTENT[help_topic]['title']}**\n\n{HELP_CONTENT[help_topic]['content']}"
            )

        # Template section
        st.divider()
        st.subheader("Templates")
        templates = get_all_templates(st.session_state)
        template_choice = st.selectbox(
            "Load a template:",
            [""] + list(templates.keys()),
            format_func=lambda x: x if x else "Select a template...",
            key="template_selector",
        )

        if template_choice and template_choice in templates:
            if st.button("Apply Template", use_container_width=True):
                tmpl = templates[template_choice]
                st.session_state["tmpl_format"] = tmpl.get("format_type", "basic")
                st.session_state["tmpl_faculty"] = tmpl.get("faculty_school", "")
                st.session_state["tmpl_project"] = tmpl.get("project_code", "")
                st.session_state["tmpl_docform"] = tmpl.get("document_form", "")
                st.session_state["tmpl_revision"] = tmpl.get("revision", "0")
                st.session_state["tmpl_extension"] = tmpl.get("extension", "pdf")
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        # Format selector
        st.subheader("Choose Naming Format")

        # Use template values if set
        default_format = st.session_state.pop("tmpl_format", "basic")
        format_options = ["basic", "advanced", "course"]
        format_type = st.radio(
            "Format",
            format_options,
            index=format_options.index(default_format) if default_format in format_options else 0,
            format_func=lambda x: {
                "basic": "Basic Format - For simple documents",
                "advanced": "Advanced Format - For departmental/project documents",
                "course": "Course-Specific Format - For educational materials",
            }[x],
            horizontal=True,
        )

        st.divider()

        # Form fields
        col_a, col_b = st.columns(2)

        with col_a:
            subject = st.text_input(
                "Subject/Activity *",
                placeholder="e.g., NamingConventions",
                help="Use PascalCase (capitalize first letter of each word, no spaces)",
            )
            # Auto-format subject
            if subject:
                subject = re.sub(r"\s+", "", subject)
                if subject:
                    subject = subject[0].upper() + subject[1:]

            date_val = st.date_input("Date *", value=datetime.now())

            default_rev = st.session_state.pop("tmpl_revision", "0")
            rev_keys = list(REVISION_STATUSES.keys())
            revision = st.selectbox(
                "Revision Status *",
                rev_keys,
                format_func=lambda x: REVISION_STATUSES[x],
                index=rev_keys.index(default_rev) if default_rev in rev_keys else 3,
            )

        with col_b:
            default_ext = st.session_state.pop("tmpl_extension", "pdf")
            ext_keys = list(FILE_EXTENSIONS.keys())
            extension = st.selectbox(
                "File Extension",
                ext_keys,
                format_func=lambda x: FILE_EXTENSIONS[x],
                index=ext_keys.index(default_ext) if default_ext in ext_keys else 0,
            )

            # Advanced fields
            if format_type in ("advanced", "course"):
                default_proj = st.session_state.pop("tmpl_project", "")
                project_code = st.text_input(
                    "Project/Account Number",
                    value=default_proj,
                    placeholder="e.g., CPE",
                    help="Optional: Control number, project code, or account identifier",
                )

                default_docform = st.session_state.pop("tmpl_docform", "")
                doc_keys = list(DOCUMENT_FORMS.keys())
                document_form = st.selectbox(
                    "Document Form",
                    doc_keys,
                    format_func=lambda x: DOCUMENT_FORMS[x],
                    index=doc_keys.index(default_docform) if default_docform in doc_keys else 0,
                )
            else:
                project_code = st.session_state.pop("tmpl_project", "")
                document_form = st.session_state.pop("tmpl_docform", "")
                project_code = ""
                document_form = ""

            # Course-specific fields
            if format_type == "course":
                default_faculty = st.session_state.pop("tmpl_faculty", "")
                faculty_school = st.text_input(
                    "Faculty-School",
                    value=default_faculty,
                    placeholder="e.g., FHSD-SoN",
                    help="Use dash to separate faculty and school",
                )

                course_code = st.text_input(
                    "Course Code",
                    placeholder="e.g., 0386-0001",
                    help="Four-digit number followed by four-digit section code",
                )

                term = st.text_input(
                    "Term Offered",
                    placeholder="e.g., 2024WT2",
                    help="Format: YYYYST (Year + Session + Term)",
                )
            else:
                st.session_state.pop("tmpl_faculty", None)
                faculty_school = ""
                course_code = ""
                term = ""

        # Buttons row
        btn_col1, btn_col2, btn_col3 = st.columns([2, 1, 1])

        with btn_col1:
            generate_clicked = st.button(
                "Generate Filename",
                type="primary",
                use_container_width=True,
            )

        with btn_col2:
            if st.button("Clear Form", use_container_width=True):
                for key in ["template_selector"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

        with btn_col3:
            save_template = st.button("Save as Template", use_container_width=True)

        # Save template dialog
        if save_template and subject:
            template_name = st.text_input("Template name:", key="new_template_name")
            if template_name and st.button("Confirm Save"):
                save_custom_template(
                    st.session_state,
                    template_name,
                    {
                        "format_type": format_type,
                        "faculty_school": faculty_school,
                        "project_code": project_code,
                        "document_form": document_form,
                        "revision": revision,
                        "extension": extension,
                    },
                )
                st.success(f"Template '{template_name}' saved!")

        if generate_clicked:
            if not subject or not date_val or not revision:
                st.error("Please fill in all required fields (Subject, Date, and Revision Status).")
            else:
                # Validate inputs
                validation_errors = validate_all_fields(
                    format_type, subject, project_code, document_form,
                    faculty_school, course_code, term,
                )

                for err in validation_errors:
                    if err.level == "error":
                        st.error(err.message)
                    elif err.level == "warning":
                        st.warning(err.message)

                if not any(e.level == "error" for e in validation_errors):
                    standard_name, sharepoint_name = generate_filename(
                        format_type, subject, date_val, revision, extension,
                        project_code, document_form, faculty_school, course_code, term,
                    )

                    # Track analytics
                    track_filename_generated(
                        st.session_state, format_type, document_form, faculty_school,
                    )

                    st.markdown('<div class="output-box">', unsafe_allow_html=True)
                    st.subheader("Generated Filename")

                    # Standard filename
                    st.text_input(
                        "CPE Standard Filename:",
                        value=standard_name,
                        key="standard_output",
                    )
                    length_check = check_filename_length(standard_name)
                    if length_check.level == "error":
                        st.error(f"\u26a0\ufe0f {length_check.message}")
                    elif length_check.level == "warning":
                        st.warning(f"\u26a0\ufe0f {length_check.message}")
                    else:
                        st.success(f"\u2713 {length_check.message}")

                    # SharePoint filename
                    st.text_input(
                        "SharePoint Filename (spaces):",
                        value=sharepoint_name,
                        key="sharepoint_output",
                    )

                    st.markdown("</div>", unsafe_allow_html=True)


# ==================== FILE LOCATION TAB ====================
with tab2:
    col1, col2 = st.columns([1, 3])

    with col1:
        st.markdown('<div class="help-panel">', unsafe_allow_html=True)
        st.subheader("Quick Guide")

        location_help_topic = st.selectbox(
            "Learn more about:",
            [""] + list(FILE_LOCATION_HELP.keys()),
            format_func=lambda x: FILE_LOCATION_HELP[x]["title"] if x else "Select a topic...",
            key="location_help",
        )

        if location_help_topic:
            st.info(
                f"**{FILE_LOCATION_HELP[location_help_topic]['title']}**\n\n"
                f"{FILE_LOCATION_HELP[location_help_topic]['content']}"
            )

        st.divider()
        st.markdown("**Common File Types:**")
        st.markdown("""
        - **Budget** - Financial records, invoices, forecasts
        - **Communications & Marketing** - Brochures, campaigns, branding
        - **Instructor Contracts** - Teaching agreements
        - **Course Management** - Syllabi, schedules, attendance
        - **Course Development** - Curriculum, learning outcomes
        """)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.subheader("Where Does This File Go?")
        st.markdown("Answer the questions below to find the correct folder location for your file.")

        st.divider()

        # Question 1: Partner-related or CPE Internal?
        is_partner_related = st.radio(
            "**Is this file tied to a specific partner (faculty/school)?**",
            [True, False],
            format_func=lambda x: "Yes - Related to a specific partner's program"
            if x
            else "No - General CPE operations",
            horizontal=True,
            key="is_partner",
        )

        st.divider()

        # Initialize variables
        cpe_block = ""
        cpe_subcat = ""
        partner = ""
        phase = ""
        subject_area = ""
        credential = ""
        applies_to_all = True
        occurrence = ""
        file_type = ""

        if not is_partner_related:
            st.markdown("### CPE Internal")

            cpe_block = st.selectbox(
                "**What function does this file support?**",
                list(CPE_INTERNAL_BLOCKS.keys()),
                format_func=lambda x: CPE_INTERNAL_BLOCKS[x],
                key="cpe_block",
            )

            if cpe_block in CPE_INTERNAL_SUBCATEGORIES:
                cpe_subcat = st.selectbox(
                    "**Select sub-category:**",
                    list(CPE_INTERNAL_SUBCATEGORIES[cpe_block].keys()),
                    format_func=lambda x: CPE_INTERNAL_SUBCATEGORIES[cpe_block][x],
                    key="cpe_subcat",
                )
        else:
            st.markdown("### Partner-Related")

            partner = st.selectbox(
                "**Which partner?**",
                list(PARTNERS.keys()),
                format_func=lambda x: PARTNERS[x],
                key="partner",
            )

            if partner:
                phase = st.radio(
                    "**Is this about developing a new program or running an active one?**",
                    ["Definition and Approvals", "Production and Delivery"],
                    format_func=lambda x: {
                        "Definition and Approvals": "Definition & Approvals - Getting a program started (proposals, market research)",
                        "Production and Delivery": "Production & Delivery - Running an active program",
                    }[x],
                    key="phase",
                )

                if phase == "Definition and Approvals":
                    subject_area = st.text_input(
                        "**Subject Area** (e.g., Nursing Foundations, Wildland Fire Management)",
                        placeholder="Enter subject area name...",
                        key="subject_area",
                    )

                    file_type = st.selectbox(
                        "**What type of file is this?**",
                        list(DEFINITION_APPROVALS_BLOCKS.keys()),
                        format_func=lambda x: DEFINITION_APPROVALS_BLOCKS[x],
                        key="def_file_type",
                    )
                else:
                    credential = st.text_input(
                        "**Credential name** (e.g., Fundamentals of Wildland Fire Ecology and Management)",
                        placeholder="Enter credential name...",
                        key="credential",
                    )

                    if credential:
                        applies_to_all = st.radio(
                            "**Does this file apply to all offerings or a specific term?**",
                            [True, False],
                            format_func=lambda x: "All offerings of this credential"
                            if x
                            else "A specific term/occurrence",
                            horizontal=True,
                            key="applies_to_all",
                        )

                        if not applies_to_all:
                            st.markdown("**Build occurrence code:**")
                            occ_col1, occ_col2, occ_col3 = st.columns(3)

                            with occ_col1:
                                occ_year = st.selectbox(
                                    "Year",
                                    [str(y) for y in range(2020, 2031)],
                                    index=5,
                                    key="occ_year",
                                )

                            with occ_col2:
                                occ_session = st.selectbox(
                                    "Session",
                                    ["W", "S"],
                                    format_func=lambda x: "W - Winter (Sept-Apr)"
                                    if x == "W"
                                    else "S - Summer (May-Aug)",
                                    key="occ_session",
                                )

                            with occ_col3:
                                occ_term = st.selectbox(
                                    "Term",
                                    ["1", "2"],
                                    format_func=lambda x: {
                                        "1": "T1 - First term",
                                        "2": "T2 - Second term",
                                    }[x],
                                    key="occ_term",
                                )

                            occurrence = f"{occ_year}{occ_session}T{occ_term}"
                            st.markdown(f"**Occurrence code:** `{occurrence}`")

                    file_type = st.selectbox(
                        "**What type of file is this?**",
                        list(PRODUCTION_DELIVERY_BLOCKS.keys()),
                        format_func=lambda x: PRODUCTION_DELIVERY_BLOCKS[x],
                        key="prod_file_type",
                    )

        st.divider()

        # Buttons row
        loc_btn_col1, loc_btn_col2 = st.columns([3, 1])

        with loc_btn_col1:
            show_location = st.button(
                "\U0001f4c1 Show File Location",
                type="primary",
                use_container_width=True,
            )

        with loc_btn_col2:
            if st.button("Clear", use_container_width=True, key="clear_location"):
                st.rerun()

        if show_location:
            # Validate inputs
            valid = True
            if not is_partner_related:
                if not cpe_block:
                    st.error("Please select a functional block.")
                    valid = False
            else:
                if not partner:
                    st.error("Please select a partner.")
                    valid = False
                elif phase == "Definition and Approvals" and not subject_area:
                    st.error("Please enter a subject area.")
                    valid = False
                elif phase == "Production and Delivery" and not credential:
                    st.error("Please enter a credential name.")
                    valid = False

            if valid:
                breadcrumb_path, folder_path = generate_file_location_path(
                    is_partner_related=is_partner_related,
                    cpe_block=cpe_block,
                    cpe_subcat=cpe_subcat,
                    partner=partner,
                    phase=phase,
                    subject_area=subject_area,
                    credential=credential,
                    applies_to_all=applies_to_all,
                    occurrence=occurrence,
                    file_type=file_type,
                )

                # Track analytics
                track_location_generated(st.session_state)

                st.markdown('<div class="location-result">', unsafe_allow_html=True)
                st.subheader("\U0001f4c1 File Location")

                st.markdown("**Navigation path:**")
                st.markdown(
                    f'<div class="location-path">{breadcrumb_path}</div>',
                    unsafe_allow_html=True,
                )

                st.markdown("**Folder structure:**")
                st.code(folder_path, language=None)

                st.text_input("Copy path:", value=folder_path, key="copy_path")

                st.markdown("</div>", unsafe_allow_html=True)

                if not is_partner_related:
                    st.info(
                        "\U0001f4a1 **Tip:** CPE Internal files are for general operations not tied to any specific partner program."
                    )
                else:
                    if phase == "Definition and Approvals":
                        st.info(
                            "\U0001f4a1 **Tip:** Definition & Approvals is for files about getting a new program started."
                        )
                    else:
                        if applies_to_all:
                            st.info(
                                "\U0001f4a1 **Tip:** Credential-level files apply to ALL offerings (e.g., master syllabus, program brochure)."
                            )
                        else:
                            st.info(
                                f"\U0001f4a1 **Tip:** This file is specific to the {occurrence} offering only."
                            )


# ==================== AI FILE ANALYZER TAB ====================
with tab3:
    col1, col2 = st.columns([2, 1])

    with col2:
        st.subheader("AI Settings")

        # AI Provider selection
        ai_provider = st.radio(
            "Choose AI Provider",
            ["gemini", "claude", "offline"],
            format_func=lambda x: {
                "gemini": "\U0001f193 Gemini (FREE)",
                "claude": "\U0001f4b0 Claude (Paid)",
                "offline": "\U0001f4e6 Offline (Rule-based)",
            }[x],
            horizontal=True,
            help="Gemini offers free API access. Offline mode works without any API key.",
        )

        api_key = ""

        if ai_provider == "gemini":
            st.success("Using Gemini 2.5 Flash via OpenRouter")

            api_key = st.text_input(
                "OpenRouter API Key",
                type="password",
                placeholder="sk-or-v1-...",
                help="Get your free API key at openrouter.ai",
            )

            if not api_key:
                try:
                    api_key = st.secrets.get("OPENROUTER_API_KEY", "")
                except Exception:
                    pass

            st.info("Get your free API key at [openrouter.ai](https://openrouter.ai/keys)")

        elif ai_provider == "claude":
            api_key = st.text_input(
                "Claude API Key",
                type="password",
                placeholder="sk-ant-...",
                help="Your Anthropic API key",
            )

            if not api_key:
                try:
                    api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
                except Exception:
                    pass

            st.info("**Note:** Claude costs approximately $0.005 per file.")

        else:
            st.info(
                "**Offline mode** uses rule-based pattern matching. "
                "No API key needed, but results may be less accurate."
            )

        privacy_level = "low"

        # How it works
        st.subheader("How it works:")
        provider_name = {"gemini": "Gemini", "claude": "Claude", "offline": "Offline"}[ai_provider]
        st.markdown(f"""
        1. Upload files below
        2. {provider_name} analyzes content
        3. Get CPE-compliant name suggestions
        """)

        # Previous results section
        saved = get_saved_results(st.session_state)
        if saved:
            st.divider()
            st.subheader("Previous Results")
            st.write(f"{len(saved)} file(s) analyzed this session")
            if st.button("Clear History", key="clear_history"):
                clear_saved_results(st.session_state)
                st.rerun()

    with col1:
        st.subheader("Upload Files")

        uploaded_files = st.file_uploader(
            "Drop files here or click to browse",
            type=SUPPORTED_FILE_TYPES,
            accept_multiple_files=True,
            help="Supported: PDF, Word, Excel, CSV, TXT, and images",
        )

        if uploaded_files:
            st.write(f"**{len(uploaded_files)} file(s) selected**")

            for i, file in enumerate(uploaded_files):
                with st.expander(f"\U0001f4c4 {file.name}", expanded=False):
                    st.write(f"Size: {file.size / 1024:.2f} KB")
                    st.write(f"Type: {file.type}")

            # Analyze button
            if ai_provider == "offline":
                button_label = f"\U0001f4e6 Analyze Files (Offline)"
            else:
                button_label = f"\U0001f916 Analyze Files with {provider_name} AI"
                if ai_provider == "gemini":
                    button_label += " (FREE)"

            if st.button(button_label, type="primary", use_container_width=True):
                if ai_provider != "offline" and not api_key:
                    if ai_provider == "gemini":
                        st.error(
                            "Please enter your OpenRouter API key. Get one free at "
                            "[openrouter.ai/keys](https://openrouter.ai/keys)"
                        )
                    else:
                        st.error(
                            "Please enter your Claude API key or configure it in Streamlit secrets."
                        )
                else:
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    results = []

                    # Initialize cache if needed
                    if "ai_cache" not in st.session_state:
                        st.session_state["ai_cache"] = {}

                    for i, file in enumerate(uploaded_files):
                        status_text.text(
                            f"Analyzing {file.name} with {provider_name}... ({i + 1}/{len(uploaded_files)})"
                        )
                        progress_bar.progress((i + 1) / len(uploaded_files))

                        # Check cache
                        file.seek(0)
                        file_hash = compute_file_hash(file)
                        cache_key = f"{ai_provider}:{file_hash}"

                        if cache_key in st.session_state["ai_cache"]:
                            result = st.session_state["ai_cache"][cache_key]
                            result["file"] = file.name
                            result["cached"] = True
                            results.append(result)
                            continue

                        # Read file content
                        file.seek(0)
                        content, content_type = read_file_content(file)

                        if content_type == "unknown":
                            results.append({
                                "file": file.name,
                                "success": False,
                                "error": "Unsupported file type",
                            })
                            continue

                        # Analyze with selected provider
                        if ai_provider == "gemini":
                            result = analyze_with_gemini(
                                api_key, content, file.name, content_type, privacy_level
                            )
                        elif ai_provider == "claude":
                            result = analyze_with_claude(
                                api_key, content, file.name, content_type, privacy_level
                            )
                        else:
                            result = analyze_with_rules(content, file.name, content_type)

                        result["file"] = file.name
                        result["cached"] = False
                        results.append(result)

                        # Cache successful results
                        if result.get("success"):
                            st.session_state["ai_cache"][cache_key] = result

                    status_text.text(f"Analysis complete with {provider_name}!")

                    # Track analytics
                    track_ai_analysis(st.session_state, ai_provider, len(uploaded_files))

                    # Save results for persistence
                    save_results(st.session_state, results)

                    # Store results in session for display
                    st.session_state["last_results"] = results

            # Display results (from session state for persistence)
            results = st.session_state.get("last_results", [])

            if results:
                st.subheader("Results")

                # Batch export button
                csv_data = export_results_to_csv(results)
                st.download_button(
                    "\U0001f4e5 Export All Results (CSV)",
                    data=csv_data,
                    file_name=f"cpe_naming_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

                st.divider()

                for result in results:
                    if result.get("success"):
                        analysis = result["analysis"]
                        format_used = analysis.get("formatUsed", "basic")
                        extracted = analysis.get("extractedFields", {})
                        confidence = analysis.get("confidence", 5)
                        conf_info = get_confidence_level(
                            confidence if isinstance(confidence, int) else 5
                        )

                        format_label = {
                            "course": "\U0001f4da Course Format",
                            "advanced": "\U0001f4cb Advanced Format",
                            "basic": "\U0001f4c4 Basic Format",
                        }.get(format_used, "\U0001f4c4 Basic Format")

                        cached_badge = " (cached)" if result.get("cached") else ""

                        st.markdown(f"""
                        <div class="file-suggestion">
                            <h4>\U0001f4c4 {result['file']}{cached_badge}</h4>
                            <p><strong>Suggested Name:</strong> <code>{analysis['suggestedName']}</code></p>
                            <p><strong>Format Used:</strong> {format_label}</p>
                            <p><strong>Confidence:</strong>
                                <span class="confidence-{conf_info['level']}">
                                    {conf_info['icon']} {confidence}/10 - {conf_info['message']}
                                </span>
                            </p>
                        </div>
                        """, unsafe_allow_html=True)

                        # Show extracted fields if available
                        if extracted:
                            with st.expander("\U0001f4cb Extracted Fields", expanded=True):
                                cols = st.columns(3)
                                with cols[0]:
                                    faculty_val = extracted.get("facultySchool") or extracted.get("faculty")
                                    if faculty_val:
                                        st.markdown(f"**Faculty-School:** {faculty_val}")
                                    if extracted.get("courseCode"):
                                        st.markdown(f"**Course:** {extracted['courseCode']}")
                                    if extracted.get("term"):
                                        st.markdown(f"**Term:** {extracted['term']}")
                                with cols[1]:
                                    if extracted.get("subject"):
                                        st.markdown(f"**Subject:** {extracted['subject']}")
                                    if extracted.get("documentForm"):
                                        st.markdown(f"**Doc Type:** {extracted['documentForm']}")
                                    if extracted.get("projectCode"):
                                        st.markdown(f"**Project:** {extracted['projectCode']}")
                                with cols[2]:
                                    if extracted.get("date"):
                                        st.markdown(f"**Date:** {extracted['date']}")
                                    if extracted.get("revision"):
                                        st.markdown(f"**Revision:** {extracted['revision']}")

                        # Show reasoning
                        with st.expander("\U0001f4ad AI Reasoning"):
                            st.write(analysis.get("reasoning", "No reasoning provided"))

                        # Copy button
                        st.text_input(
                            "Copy suggested name:",
                            value=analysis["suggestedName"],
                            key=f"copy_{result['file']}",
                        )

                        st.divider()
                    else:
                        st.error(
                            f"\u274c **{result['file']}**: {result.get('error', 'Unknown error')}"
                        )
        else:
            st.info("\U0001f446 Upload files to get started with AI analysis")


# ==================== DASHBOARD TAB ====================
with tab4:
    st.subheader("\U0001f4ca Session Dashboard")

    analytics = get_analytics_summary(st.session_state)

    # Summary metrics
    met_col1, met_col2, met_col3, met_col4 = st.columns(4)

    with met_col1:
        st.metric("Filenames Generated", analytics["filenames_generated"])

    with met_col2:
        st.metric("Files Analyzed (AI)", analytics["files_analyzed"])

    with met_col3:
        st.metric("Locations Found", analytics["locations_generated"])

    with met_col4:
        total_actions = (
            analytics["filenames_generated"]
            + analytics["files_analyzed"]
            + analytics["locations_generated"]
        )
        st.metric("Total Actions", total_actions)

    st.divider()

    dash_col1, dash_col2 = st.columns(2)

    with dash_col1:
        st.markdown("#### Format Usage")
        formats = analytics["formats_used"]
        if any(formats.values()):
            for fmt, count in formats.items():
                label = {"basic": "Basic", "advanced": "Advanced", "course": "Course"}[fmt]
                st.write(f"**{label}:** {count} uses")
        else:
            st.write("No filenames generated yet.")

        st.markdown("#### AI Provider Usage")
        providers = analytics["ai_provider_used"]
        if any(providers.values()):
            for prov, count in providers.items():
                label = {"gemini": "Gemini (Free)", "claude": "Claude (Paid)", "offline": "Offline"}[prov]
                st.write(f"**{label}:** {count} files")
        else:
            st.write("No AI analyses yet.")

    with dash_col2:
        st.markdown("#### Most Used Document Forms")
        doc_forms = analytics["document_forms_used"]
        if doc_forms:
            sorted_forms = sorted(doc_forms.items(), key=lambda x: -x[1])
            for form, count in sorted_forms[:10]:
                form_name = DOCUMENT_FORMS.get(form, form)
                st.write(f"**{form_name}:** {count}")
        else:
            st.write("No document forms tracked yet.")

        st.markdown("#### Partner Usage")
        partners = analytics["partners_used"]
        if partners:
            sorted_partners = sorted(partners.items(), key=lambda x: -x[1])
            for p, count in sorted_partners[:10]:
                st.write(f"**{p}:** {count}")
        else:
            st.write("No partner data yet.")

    st.divider()
    st.caption(f"Session started: {analytics.get('session_start', 'N/A')}")

    # Manage custom templates
    st.divider()
    st.subheader("Manage Custom Templates")

    custom_templates = st.session_state.get("custom_templates", {})
    if custom_templates:
        for name in list(custom_templates.keys()):
            col_t1, col_t2 = st.columns([4, 1])
            with col_t1:
                st.write(f"\U0001f4c4 **{name}** - {custom_templates[name].get('format_type', 'basic')} format")
            with col_t2:
                if st.button("Delete", key=f"del_tmpl_{name}"):
                    delete_custom_template(st.session_state, name)
                    st.rerun()
    else:
        st.write("No custom templates saved. Use 'Save as Template' in the Manual Generator tab.")


# ─── Footer ────────────────────────────────────────────────────────────────

st.divider()
st.markdown("""
<div style="text-align: center; color: #666; font-size: 12px;">
    <p>UBC CPE File Naming Tool V3 | Powered by Gemini AI (Free), Claude AI & Offline Mode</p>
    <p>For use by UBC Continuing Professional Education staff</p>
    <p style="font-size: 10px;">Keyboard shortcuts: Tab to navigate fields | Enter to submit forms</p>
</div>
""", unsafe_allow_html=True)
