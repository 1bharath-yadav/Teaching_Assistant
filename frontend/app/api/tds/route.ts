import { NextRequest, NextResponse } from "next/server";
import { getServerSideConfig } from "@/app/config/server";
import { TDS_API_BASE_URL, TDS_API_ENDPOINT, ModelProvider } from "@/app/constant";
import { prettyObject } from "@/app/utils/format";
import { auth } from "@/app/api/auth";

const serverConfig = getServerSideConfig();

async function handle(req: NextRequest) {
  console.log("[TDS Route] handling request");

  if (req.method === "OPTIONS") {
    return NextResponse.json({ body: "OK" }, { status: 200 });
  }

  const authResult = auth(req, ModelProvider.TDS);
  if (authResult.error) {
    return NextResponse.json(authResult, {
      status: 401,
    });
  }

  try {
    const response = await requestTDS(req);
    return response;
  } catch (e) {
    console.error("[TDS API] ", e);
    return NextResponse.json(prettyObject(e));
  }
}

async function requestTDS(req: NextRequest) {
  const controller = new AbortController();

  // Get the base URL from environment or use default
  let baseUrl = serverConfig.customApiBaseUrl || TDS_API_BASE_URL;

  if (!baseUrl.startsWith("http")) {
    baseUrl = `http://${baseUrl}`;
  }

  if (baseUrl.endsWith("/")) {
    baseUrl = baseUrl.slice(0, -1);
  }

  console.log("[TDS Base Url]", baseUrl);

  const timeoutId = setTimeout(
    () => {
      controller.abort();
    },
    60 * 1000, // 60 second timeout
  );

  const fetchUrl = `${baseUrl}${TDS_API_ENDPOINT}`;
  const body = await req.text();

  console.log("[TDS Request]", fetchUrl, body);

  const fetchOptions: RequestInit = {
    headers: {
      "Content-Type": "application/json",
      ...getHeaders(),
    },
    method: req.method,
    body,
    redirect: "manual",
    signal: controller.signal,
  };

  try {
    const res = await fetch(fetchUrl, fetchOptions);

    // Handle response
    const newHeaders = new Headers(res.headers);
    newHeaders.delete("www-authenticate");
    // to disable nginx buffering
    newHeaders.set("X-Accel-Buffering", "no");

    return new Response(res.body, {
      status: res.status,
      statusText: res.statusText,
      headers: newHeaders,
    });
  } finally {
    clearTimeout(timeoutId);
  }
}

function getHeaders() {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  // Add any additional headers if needed
  const customApiKey = serverConfig.customApiKey;
  if (customApiKey) {
    headers["Authorization"] = `Bearer ${customApiKey}`;
  }

  return headers;
}

export const GET = handle;
export const POST = handle;

export const runtime = "edge";
