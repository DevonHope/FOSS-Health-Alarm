package io.github.devonhope.nudgeband.ui

import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.time.format.FormatStyle

private val timeFormat = DateTimeFormatter.ofLocalizedTime(FormatStyle.SHORT)
private val dateFormat = DateTimeFormatter.ofPattern("EEE d MMM")

fun formatTime(utc: Long): String = timeFormat.format(Instant.ofEpochSecond(utc).atZone(ZoneId.systemDefault()))
fun formatDate(utc: Long): String = dateFormat.format(Instant.ofEpochSecond(utc).atZone(ZoneId.systemDefault()))
fun formatTime(hour: Int, minute: Int): String = timeFormat.format(java.time.LocalTime.of(hour, minute))
fun formatMinutes(minutes: Int): String = if (minutes >= 60) "${minutes / 60} h ${minutes % 60} min" else "$minutes min"
