import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { emails } from '@/lib/schema'
import { eq } from 'drizzle-orm'
import { verifyToken, getTokenFromHeader } from '@/lib/auth-utils'
import { v4 as uuidv4 } from 'uuid'

export async function GET(request: NextRequest) {
  try {
    const authHeader = request.headers.get('authorization')
    const token = getTokenFromHeader(authHeader)

    if (!token) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      )
    }

    const payload = verifyToken(token)
    if (!payload) {
      return NextResponse.json(
        { error: 'Invalid token' },
        { status: 401 }
      )
    }

    const userEmails = await db
      .select()
      .from(emails)
      .where(eq(emails.userId, payload.userId))

    return NextResponse.json(userEmails)
  } catch (error) {
    console.error('Error fetching emails:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const authHeader = request.headers.get('authorization')
    const token = getTokenFromHeader(authHeader)

    if (!token) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      )
    }

    const payload = verifyToken(token)
    if (!payload) {
      return NextResponse.json(
        { error: 'Invalid token' },
        { status: 401 }
      )
    }

    const body = await request.json()
    const { to, subject, body: emailBody } = body

    if (!to || !subject) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      )
    }

    const newEmail = await db
      .insert(emails)
      .values({
        id: uuidv4(),
        userId: payload.userId,
        from: payload.email,
        to,
        subject,
        body: emailBody || '',
        isDraft: true,
      })
      .returning()

    return NextResponse.json(newEmail[0], { status: 201 })
  } catch (error) {
    console.error('Error creating email:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
