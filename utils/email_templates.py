"""
Email templates for transactional emails.

Brand theme: deep navy (#1a1a2e) header, electric blue (#4361ee) primary CTA.
Action buttons: green (#22c55e) for confirm, red (#ef4444) for destructive/deny.
"""

_BASE_STYLES = """
  body { margin:0; padding:0; background-color:#f4f6f8; font-family:Arial,sans-serif; }
"""


def _wrap(content: str, header_color: str = "#1a1a2e") -> str:
    """Wrap email content in the shared card layout."""
    return f"""
    <html>
    <head><style>{_BASE_STYLES}</style></head>
    <body style="margin:0;padding:0;background-color:#f4f6f8;font-family:Arial,sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f6f8;padding:40px 0;">
        <tr>
          <td align="center">
            <table width="540" cellpadding="0" cellspacing="0"
                   style="background-color:#ffffff;border-radius:10px;overflow:hidden;
                          box-shadow:0 4px 16px rgba(0,0,0,0.10);">

              <!-- Header -->
              <tr>
                <td style="background-color:{header_color};padding:32px 40px;text-align:center;">
                  <h1 style="margin:0;color:#ffffff;font-size:22px;font-weight:700;letter-spacing:1px;">
                    E-Commerce App
                  </h1>
                </td>
              </tr>

              <!-- Body -->
              <tr>
                <td style="padding:40px;">
                  {content}
                </td>
              </tr>

              <!-- Footer -->
              <tr>
                <td style="background-color:#f9fafb;padding:18px 40px;border-top:1px solid #e5e7eb;text-align:center;">
                  <p style="margin:0;color:#9ca3af;font-size:12px;">
                    This is an automated message &mdash; please do not reply.
                  </p>
                </td>
              </tr>

            </table>
          </td>
        </tr>
      </table>
    </body>
    </html>
    """


def _button(label: str, url: str, color: str) -> str:
    return f"""
    <table cellpadding="0" cellspacing="0" style="margin:0 auto;">
      <tr>
        <td style="border-radius:6px;background-color:{color};">
          <a href="{url}"
             style="display:inline-block;padding:13px 32px;color:#ffffff;text-decoration:none;
                    font-size:14px;font-weight:700;border-radius:6px;">
            {label}
          </a>
        </td>
      </tr>
    </table>
    """


def _warning_box(text: str, border_color: str = "#f59e0b", bg_color: str = "#fff8e1", text_color: str = "#92600a") -> str:
    return f"""
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td style="background-color:{bg_color};border-left:4px solid {border_color};
                   border-radius:4px;padding:14px 16px;">
          <p style="margin:0;color:{text_color};font-size:13px;line-height:1.6;">{text}</p>
        </td>
      </tr>
    </table>
    """


def verification_email(code: str) -> str:
    content = f"""
      <h2 style="margin:0 0 10px;color:#1a1a2e;font-size:20px;">Verify Your Email</h2>
      <p style="margin:0 0 28px;color:#4b5563;font-size:15px;line-height:1.6;">
        Welcome! Use the code below to verify your email address.
        It expires in <strong>10 minutes</strong>.
      </p>

      <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:28px;">
        <tr>
          <td align="center"
              style="background-color:#f0f4ff;border:2px dashed #4361ee;
                     border-radius:8px;padding:28px;">
            <span style="font-size:40px;font-weight:700;letter-spacing:12px;color:#1a1a2e;">
              {code}
            </span>
          </td>
        </tr>
      </table>

      <p style="margin:0;color:#9ca3af;font-size:13px;line-height:1.6;">
        If you didn't create an account, you can safely ignore this email.
      </p>
    """
    return _wrap(content)


def password_reset_email(reset_url: str) -> str:
    content = f"""
      <h2 style="margin:0 0 10px;color:#1a1a2e;font-size:20px;">Reset Your Password</h2>
      <p style="margin:0 0 28px;color:#4b5563;font-size:15px;line-height:1.6;">
        We received a request to reset your password.
        Click the button below &mdash; this link expires in <strong>15 minutes</strong>.
      </p>

      <div style="text-align:center;margin-bottom:28px;">
        {_button("Reset Password", reset_url, "#4361ee")}
      </div>

      {_warning_box("<strong>Didn't request this?</strong> Ignore this email &mdash; your password will remain unchanged.")}

      <p style="margin:20px 0 0;color:#9ca3af;font-size:12px;line-height:1.6;">
        Or copy this link into your browser:<br>
        <span style="color:#4361ee;">{reset_url}</span>
      </p>
    """
    return _wrap(content)


def password_change_request_email(confirm_url: str, deny_url: str) -> str:
    content = f"""
      <h2 style="margin:0 0 10px;color:#1a1a2e;font-size:20px;">Password Change Request</h2>
      <p style="margin:0 0 28px;color:#4b5563;font-size:15px;line-height:1.6;">
        A password change was requested for your account. Was this you?
      </p>

      <!-- Confirm -->
      <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:14px;">
        <tr>
          <td style="background-color:#f0fdf4;border-radius:8px;padding:20px;text-align:center;">
            <p style="margin:0 0 14px;color:#1a1a2e;font-size:14px;font-weight:700;">
              Yes, this was me
            </p>
            {_button("Confirm Password Change", confirm_url, "#22c55e")}
          </td>
        </tr>
      </table>

      <!-- Deny -->
      <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:28px;">
        <tr>
          <td style="background-color:#fff5f5;border-radius:8px;padding:20px;text-align:center;">
            <p style="margin:0 0 14px;color:#1a1a2e;font-size:14px;font-weight:700;">
              No, this was NOT me
            </p>
            {_button("Deny &amp; Logout All Sessions", deny_url, "#ef4444")}
          </td>
        </tr>
      </table>

      <p style="margin:0;color:#9ca3af;font-size:12px;line-height:1.8;">
        This link expires in 15 minutes.<br>
        Confirm: <span style="color:#22c55e;">{confirm_url}</span><br>
        Deny: <span style="color:#ef4444;">{deny_url}</span>
      </p>
    """
    return _wrap(content)


def password_change_denied_email() -> str:
    content = """
      <h2 style="margin:0 0 10px;color:#1a1a2e;font-size:20px;">Password Change Denied</h2>
      <p style="margin:0 0 24px;color:#4b5563;font-size:15px;line-height:1.6;">
        A password change request for your account was denied and all active sessions
        have been logged out.
      </p>

      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td style="background-color:#fff5f5;border-left:4px solid #ef4444;
                     border-radius:4px;padding:14px 16px;">
            <p style="margin:0;color:#b91c1c;font-size:13px;line-height:1.6;">
              <strong>If you did not initiate this request</strong>, your account may be at risk.
              Please log in and update your password immediately.
            </p>
          </td>
        </tr>
      </table>
    """
    return _wrap(content, header_color="#b91c1c")
