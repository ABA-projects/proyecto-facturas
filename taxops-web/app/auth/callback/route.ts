import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const access_token = searchParams.get("access_token");
  const refresh_token = searchParams.get("refresh_token");

  if (!access_token || !refresh_token) {
    return NextResponse.redirect(new URL("/login?error=oauth_failed", request.url));
  }

  // Store access token in a readable cookie so the client can pick it up
  const response = NextResponse.redirect(new URL("/dashboard", request.url));

  response.cookies.set("taxops_access_pending", access_token, {
    httpOnly: false, // must be readable by JS to move to sessionStorage
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    maxAge: 60, // only needed for 1 redirect
    path: "/",
  });

  response.cookies.set("taxops_refresh", refresh_token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    maxAge: 60 * 60 * 24 * 7,
    path: "/",
  });

  return response;
}
